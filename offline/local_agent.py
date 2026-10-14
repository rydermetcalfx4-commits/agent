#!/usr/bin/env python3
"""A minimal offline coding agent: a local model + a tool loop + this repo's memory.

Talks to any OpenAI-compatible local server (Ollama, llama.cpp's llama-server, LM Studio, vLLM),
so nothing leaves your machine. Standard library only.

  python3 offline/local_agent.py "list the python files and summarise scripts/doctor.py"
  python3 offline/local_agent.py                     # interactive
  AGENT_MODEL=qwen3-coder:30b python3 offline/local_agent.py ...

Environment:
  AGENT_BASE_URL  default http://localhost:11434/v1   (Ollama; llama-server is http://localhost:8080/v1)
  AGENT_MODEL     default qwen3:8b                    (any tool-capable model you have pulled)
  AGENT_YES=1     run shell commands without asking (only in a sandbox you trust)

It is the same loop Claude Code runs, stripped to the bone: send messages + tool schemas,
run whatever tools the model asks for, append the results, repeat until it answers in text.
It loads lessons from memory/learnings.md (or .evolving-agent/learnings.md), refuses what
scripts/guard.py refuses, and logs failed tool calls where /evolve will find them.
"""
import json, os, re, subprocess, sys, urllib.request
from datetime import date
from pathlib import Path

ROOT = Path.cwd()
BASE_URL = os.environ.get("AGENT_BASE_URL", "http://localhost:11434/v1").rstrip("/")
MODEL = os.environ.get("AGENT_MODEL", "qwen3:8b")
AUTO_YES = os.environ.get("AGENT_YES") == "1"
MAX_TURNS = 25
OUTPUT_LIMIT = 12_000

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
try:  # reuse the repo's guard when available
    from guard import push_problem, rm_problem, secret_problem
except ImportError:  # running outside this repo
    rm_problem = push_problem = lambda cmd: None
    secret_problem = lambda tool, inp: None


# ---- memory -----------------------------------------------------------------
def memory_paths():
    for d in (ROOT / "memory", ROOT / ".evolving-agent"):
        if (d / "learnings.md").exists():
            return d / "learnings.md", d / "failures.log"
    return None, ROOT / ".evolving-agent" / "failures.log"


def lessons(min_conf=0.7):
    path, _ = memory_paths()
    if not path:
        return []
    out = []
    for line in path.read_text().splitlines():
        m = re.match(r"^- \[(0\.\d|1\.0)\] \d{4}-\d{2}-\d{2} — (.+)$", line)
        if m and float(m.group(1)) >= min_conf:
            out.append(m.group(2))
    return out


def log_failure(tool, what, error):
    _, path = memory_paths()
    path.parent.mkdir(parents=True, exist_ok=True)
    one = lambda s, n: re.sub(r"\s+", " ", str(s)).strip()[:n]
    with path.open("a") as f:
        f.write(f"{date.today()} | {tool} | {one(what, 120)} | {one(error, 200)}\n")


# ---- tools ------------------------------------------------------------------
def _inside(path):
    p = (ROOT / path).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise ValueError(f"{path} is outside the project")
    return p


def read_file(path):
    if (why := secret_problem("Read", {"file_path": path})):
        raise PermissionError(why)
    return _inside(path).read_text(errors="replace")[:OUTPUT_LIMIT]


def write_file(path, content):
    if (why := secret_problem("Write", {"file_path": path})):
        raise PermissionError(why)
    p = _inside(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"wrote {len(content)} chars to {path}"


def list_files(path="."):
    p = _inside(path)
    skip = {".git", "node_modules", "__pycache__", ".venv"}
    names = [str(f.relative_to(ROOT)) for f in sorted(p.rglob("*")) if f.is_file() and not skip & set(f.parts)]
    return "\n".join(names[:500]) + ("\n…" if len(names) > 500 else "")


def run_shell(command):
    if (why := rm_problem(command) or push_problem(command) or secret_problem("Bash", {"command": command})):
        raise PermissionError(f"blocked by guard: {why}")
    if not AUTO_YES and input(f"\n$ {command}\nrun it? [y/N] ").strip().lower() != "y":
        return "the user declined to run this command"
    r = subprocess.run(command, shell=True, cwd=ROOT, capture_output=True, text=True, timeout=300)
    out = (r.stdout + r.stderr)[-OUTPUT_LIMIT:]
    if r.returncode != 0:
        raise RuntimeError(f"exit {r.returncode}\n{out}")
    return out or "(no output)"


TOOLS = {"read_file": read_file, "write_file": write_file, "list_files": list_files, "run_shell": run_shell}
SCHEMAS = [
    {"type": "function", "function": {"name": "read_file", "description": "Read a text file in the project.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "write_file", "description": "Create or overwrite a file in the project.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                    "required": ["path", "content"]}}},
    {"type": "function", "function": {"name": "list_files", "description": "List files under a directory of the project.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "run_shell", "description": "Run a shell command in the project root (the user may be asked first).",
     "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
]


def system_prompt():
    text = (f"You are a careful offline coding agent working in {ROOT}. Use the tools to inspect before you change "
            "anything, make the smallest change that does the job, and run a check before saying it works. "
            "When you are done, answer in plain text without calling tools.")
    learned = lessons()
    if learned:
        text += "\n\nLessons learned in this project (apply them):\n" + "\n".join(f"- {l}" for l in learned)
    return text


# ---- the loop ---------------------------------------------------------------
def chat(messages):
    body = json.dumps({"model": MODEL, "messages": messages, "tools": SCHEMAS, "temperature": 0.2}).encode()
    req = urllib.request.Request(f"{BASE_URL}/chat/completions", body,
                                 {"Content-Type": "application/json", "Authorization": "Bearer local"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)["choices"][0]["message"]


def run_turn(messages, say=print):
    for _ in range(MAX_TURNS):
        msg = chat(messages)
        calls = msg.get("tool_calls") or []
        messages.append({"role": "assistant", "content": msg.get("content") or "", **({"tool_calls": calls} if calls else {})})
        if not calls:
            return msg.get("content") or ""
        for call in calls:
            name = call["function"]["name"]
            try:
                args = call["function"].get("arguments") or {}
                args = json.loads(args) if isinstance(args, str) else args
                say(f"  → {name}({', '.join(f'{k}={str(v)[:60]!r}' for k, v in args.items())})")
                result = TOOLS[name](**args)
            except Exception as e:  # the model sees the error and can recover
                result = f"ERROR: {type(e).__name__}: {e}"
                log_failure(name, json.dumps(args if isinstance(args, dict) else {})[:200], result)
            messages.append({"role": "tool", "tool_call_id": call.get("id", name), "name": name, "content": str(result)})
    return "(stopped: too many tool calls in one turn)"


def main():
    messages = [{"role": "system", "content": system_prompt()}]
    print(f"local agent · model {MODEL} at {BASE_URL} · {len(lessons())} lessons loaded")
    prompts = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else None
    while True:
        text = prompts.pop(0) if prompts else (None if prompts == [] else input("\nyou> ").strip())
        if not text or text in ("exit", "quit"):
            return
        messages.append({"role": "user", "content": text})
        try:
            print("\n" + run_turn(messages))
        except OSError as e:
            sys.exit(f"cannot reach {BASE_URL} ({e}). Is the model server running? e.g. `ollama serve`")


if __name__ == "__main__":
    main()
