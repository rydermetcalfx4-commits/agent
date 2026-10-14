#!/usr/bin/env python3
"""End-to-end test of local_agent.py against a scripted fake OpenAI-compatible server (no model needed).

  python3 offline/test_local_agent.py
"""
import json, os, sys, tempfile, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

SCRIPT = []      # replies the fake model gives, in order
RECEIVED = []    # request bodies it saw


class FakeModel(BaseHTTPRequestHandler):
    def do_POST(self):
        RECEIVED.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        body = json.dumps({"choices": [{"message": SCRIPT.pop(0)}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def call(name, **args):
    return {"id": f"c-{name}", "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


class LocalAgentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), FakeModel)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.tmp = tempfile.TemporaryDirectory()
        project = Path(cls.tmp.name)
        (project / "memory").mkdir()
        (project / "memory" / "learnings.md").write_text(
            "- [0.9] 2026-10-14 — Strong lesson.\n- [0.4] 2026-10-14 — Weak lesson.\n")
        (project / "hello.txt").write_text("hi there")
        (project / ".env").write_text("SECRET=1")
        os.environ["AGENT_BASE_URL"] = f"http://127.0.0.1:{cls.server.server_port}/v1"
        os.environ["AGENT_YES"] = "1"
        os.chdir(project)
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import local_agent
        cls.agent = local_agent
        cls.agent.ROOT = project.resolve()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.tmp.cleanup()

    def setUp(self):
        SCRIPT.clear()
        RECEIVED.clear()

    def run_turn(self, prompt):
        messages = [{"role": "system", "content": self.agent.system_prompt()}, {"role": "user", "content": prompt}]
        return self.agent.run_turn(messages, say=lambda *_: None), messages

    def test_tool_loop_reads_writes_and_answers(self):
        SCRIPT[:] = [
            {"content": "", "tool_calls": [call("read_file", path="hello.txt")]},
            {"content": "", "tool_calls": [call("write_file", path="out/copy.txt", content="hi there")]},
            {"content": "Copied it."},
        ]
        answer, messages = self.run_turn("copy hello.txt")
        self.assertEqual(answer, "Copied it.")
        self.assertEqual((self.agent.ROOT / "out" / "copy.txt").read_text(), "hi there")
        tool_results = [m["content"] for m in messages if m["role"] == "tool"]
        self.assertEqual(tool_results[0], "hi there")
        self.assertEqual(len(RECEIVED), 3)
        self.assertEqual({t["function"]["name"] for t in RECEIVED[0]["tools"]},
                         {"read_file", "write_file", "list_files", "run_shell"})

    def test_lessons_reach_the_system_prompt(self):
        prompt = self.agent.system_prompt()
        self.assertIn("Strong lesson.", prompt)
        self.assertNotIn("Weak lesson.", prompt)

    def test_guard_blocks_and_failure_is_logged(self):
        SCRIPT[:] = [
            {"content": "", "tool_calls": [call("read_file", path=".env"), call("run_shell", command="rm -rf ~")]},
            {"content": "I can't do that."},
        ]
        answer, messages = self.run_turn("show secrets and wipe home")
        self.assertEqual(answer, "I can't do that.")
        results = [m["content"] for m in messages if m["role"] == "tool"]
        self.assertTrue(all(r.startswith("ERROR: PermissionError") for r in results), results)
        log = (self.agent.ROOT / "memory" / "failures.log").read_text()
        self.assertIn("| read_file |", log)
        self.assertIn("| run_shell |", log)

    def test_paths_outside_project_are_refused(self):
        SCRIPT[:] = [{"content": "", "tool_calls": [call("read_file", path="../../etc/passwd")]}, {"content": "no"}]
        _, messages = self.run_turn("read passwd")
        self.assertIn("outside the project", [m for m in messages if m["role"] == "tool"][0]["content"])

    def test_shell_runs_and_failures_come_back_as_errors(self):
        SCRIPT[:] = [{"content": "", "tool_calls": [call("run_shell", command="echo ok"),
                                                    call("run_shell", command="exit 3")]}, {"content": "done"}]
        _, messages = self.run_turn("run things")
        results = [m["content"] for m in messages if m["role"] == "tool"]
        self.assertEqual(results[0].strip(), "ok")
        self.assertIn("exit 3", results[1])

    def test_runaway_loops_stop(self):
        SCRIPT[:] = [{"content": "", "tool_calls": [call("list_files")]}] * self.agent.MAX_TURNS
        answer, _ = self.run_turn("loop forever")
        self.assertIn("too many tool calls", answer)


if __name__ == "__main__":
    unittest.main(verbosity=2)
