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

Tracing (optional): with `pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-http` and
OTEL_EXPORTER_OTLP_ENDPOINT set, each turn is traced with OTel GenAI conventions (invoke_agent → chat /
execute_tool). For Honeycomb: OTEL_EXPORTER_OTLP_ENDPOINT=https://api.honeycomb.io and
OTEL_EXPORTER_OTLP_HEADERS=x-honeycomb-team=<ingest key>. Prompts and replies are recorded only with
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=span_only.

It is the same loop Claude Code runs, stripped to the bone: send messages + tool schemas,
run whatever tools the model asks for, append the results, repeat until it answers in text.
It loads lessons from memory/learnings.md (or .evolving-agent/learnings.md), refuses what
scripts/guard.py refuses, and logs failed tool calls where /evolve will find them.
"""
import json, os, re, subprocess, sys, urllib.request, uuid
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

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


# ---- telemetry (optional) ---------------------------------------------------
CONVERSATION_ID = str(uuid.uuid4())  # one per process: every turn of this session shares it
CAPTURE = os.environ.get("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "") in ("span_only", "span_and_event", "true")
CONTENT_LIMIT = 4_000


def _tracer():
    if not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return None, lambda: None
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        print("tracing off: pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-http", file=sys.stderr)
        return None, lambda: None
    processor = BatchSpanProcessor(OTLPSpanExporter())
    provider = TracerProvider(resource=Resource.create({"service.name": os.environ.get("OTEL_SERVICE_NAME", "local-agent")}))
    provider.add_span_processor(processor)
    return provider.get_tracer("local_agent"), processor.force_flush


TRACER, flush_telemetry = _tracer()


@contextmanager
def span(name, kind, attrs):
    """A GenAI span, or None when tracing is off. Exceptions mark it as an error and propagate."""
    if not TRACER:
        yield None
        return
    from opentelemetry.trace import SpanKind
    attrs = {"gen_ai.conversation.id": CONVERSATION_ID, **attrs}
    with TRACER.start_as_current_span(name, kind=getattr(SpanKind, kind), attributes=attrs) as s:
        try:
            yield s
        except Exception as e:
            s.set_attribute("error.type", type(e).__name__)
            raise


def fail(s, e):
    if s:
        from opentelemetry.trace import Status, StatusCode
        s.set_attribute("error.type", type(e).__name__)
        s.set_status(Status(StatusCode.ERROR, str(e)[:200]))


def as_otel_messages(messages):
    """OpenAI-style chat messages → the GenAI semconv role/parts shape, as truncated JSON."""
    out = []
    for m in messages:
        if m["role"] == "tool":
            parts = [{"type": "tool_call_response", "id": m.get("tool_call_id"), "response": m.get("content")}]
        else:
            parts = [{"type": "text", "content": m["content"]}] if m.get("content") else []
            parts += [{"type": "tool_call", "id": c.get("id"), "name": c["function"]["name"],
                       "arguments": c["function"].get("arguments")} for c in m.get("tool_calls") or []]
        out.append({"role": m["role"], "parts": parts})
    return json.dumps(out)[:CONTENT_LIMIT]


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
    url = urlparse(BASE_URL)
    attrs = {"gen_ai.operation.name": "chat", "gen_ai.request.model": MODEL, "gen_ai.request.temperature": 0.2,
             "server.address": url.hostname or "", "server.port": url.port or (443 if url.scheme == "https" else 80)}
    if CAPTURE:
        attrs["gen_ai.input.messages"] = as_otel_messages(messages)
    with span(f"chat {MODEL}", "CLIENT", attrs) as s:
        with urllib.request.urlopen(req, timeout=600) as r:
            data = json.load(r)
        choice = data["choices"][0]
        if s:
            usage = data.get("usage") or {}
            for key, value in (("gen_ai.response.model", data.get("model")), ("gen_ai.response.id", data.get("id")),
                               ("gen_ai.usage.input_tokens", usage.get("prompt_tokens")),
                               ("gen_ai.usage.output_tokens", usage.get("completion_tokens"))):
                if value is not None:
                    s.set_attribute(key, value)
            if choice.get("finish_reason"):
                s.set_attribute("gen_ai.response.finish_reasons", [choice["finish_reason"]])
            if CAPTURE:
                s.set_attribute("gen_ai.output.messages", as_otel_messages([choice["message"]]))
        return choice["message"]


def run_turn(messages, say=print):
    attrs = {"gen_ai.operation.name": "invoke_agent", "gen_ai.agent.name": "local-agent", "gen_ai.request.model": MODEL}
    with span("invoke_agent local-agent", "INTERNAL", attrs) as s:
        answer = _run_turn(messages, say)
        if s and CAPTURE:
            s.set_attribute("gen_ai.output.messages", as_otel_messages([{"role": "assistant", "content": answer}]))
        return answer


def _run_turn(messages, say):
    for _ in range(MAX_TURNS):
        msg = chat(messages)
        calls = msg.get("tool_calls") or []
        messages.append({"role": "assistant", "content": msg.get("content") or "", **({"tool_calls": calls} if calls else {})})
        if not calls:
            return msg.get("content") or ""
        for call in calls:
            name = call["function"]["name"]
            attrs = {"gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": name, "gen_ai.tool.type": "function",
                     "gen_ai.tool.call.id": call.get("id", name), "gen_ai.agent.name": "local-agent",
                     "gen_ai.tool.call.arguments": str(call["function"].get("arguments") or "{}")[:CONTENT_LIMIT]}
            with span(f"execute_tool {name}", "INTERNAL", attrs) as s:
                try:
                    args = call["function"].get("arguments") or {}
                    args = json.loads(args) if isinstance(args, str) else args
                    say(f"  → {name}({', '.join(f'{k}={str(v)[:60]!r}' for k, v in args.items())})")
                    result = TOOLS[name](**args)
                except Exception as e:  # the model sees the error and can recover
                    result = f"ERROR: {type(e).__name__}: {e}"
                    log_failure(name, json.dumps(args if isinstance(args, dict) else {})[:200], result)
                    fail(s, e)
                if s:
                    s.set_attribute("gen_ai.tool.call.result", str(result)[:CONTENT_LIMIT])
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
        finally:
            flush_telemetry()  # short CLI runs exit before the batch exporter's timer fires


if __name__ == "__main__":
    main()
