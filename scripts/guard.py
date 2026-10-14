#!/usr/bin/env python3
"""PreToolUse guard: block a few catastrophic or secret-leaking tool calls.

Exit 2 blocks the call and shows the reason to Claude, which should then ask the user.
Deliberately narrow so it never gets in the way of normal work.
Idea from disler/claude-code-hooks-mastery; implementation is our own.
"""
import json, re, shlex, sys
from pathlib import Path

DANGEROUS_RM_TARGETS = {"/", "/*", "~", "~/", "~/*", "$HOME", "$HOME/", "${HOME}", ".", "./", "..", "../", "*", ".*", ".git"}
SECRET_FILE = re.compile(r"(^|/)\.env(\.[\w-]+)?$")
SECRET_OK = re.compile(r"\.(example|sample|template|dist)$")
READERS = {"cat", "less", "more", "head", "tail", "bat", "batcat", "cp", "scp", "base64", "xxd", "strings", "source", "."}


def segments(cmd):
    """Split a shell command into word lists, one per simple command; heredoc bodies are dropped."""
    cmd = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?.*?^\s*\1\s*$", "", cmd, flags=re.S | re.M)
    for part in re.split(r"&&|\|\||;|\||\n", cmd):
        try:
            words = shlex.split(part, posix=True)
        except ValueError:
            words = part.split()
        if words:
            yield words


def rm_problem(cmd):
    for words in segments(cmd):
        if "rm" not in words:
            continue
        args = words[words.index("rm") + 1:]
        flags = "".join(a.lstrip("-") for a in args if a.startswith("-") and not a.startswith("--"))
        recursive = "r" in flags.lower() or "--recursive" in args
        targets = [a for a in args if not a.startswith("-")]
        if recursive and any(t.rstrip() in DANGEROUS_RM_TARGETS for t in targets):
            return f"recursive rm on {', '.join(t for t in targets if t in DANGEROUS_RM_TARGETS)}"
    return None


def push_problem(cmd):
    for words in segments(cmd):
        if words[:2] == ["git", "push"] and any(w in ("--force", "-f") for w in words) \
                and any(w.split(":")[-1] in ("main", "master") for w in words[2:]):
            return "force push to main/master"
    return None


def secret_problem(tool, inp):
    paths = []
    if tool in ("Read", "Edit", "Write", "MultiEdit", "NotebookEdit"):
        paths.append(inp.get("file_path") or inp.get("notebook_path") or "")
    elif tool == "Bash":
        # only arguments of a reading command count; text in heredocs, messages, or other args doesn't
        for words in segments(inp.get("command", "")):
            if words and Path(words[0]).name in READERS:
                paths += [w for w in words[1:] if not w.startswith("-")]
    for p in paths:
        if SECRET_FILE.search(p) and not SECRET_OK.search(p):
            return f"access to secrets file {p}"
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    tool, inp = data.get("tool_name", ""), data.get("tool_input") or {}
    problem = secret_problem(tool, inp)
    if tool == "Bash":
        cmd = inp.get("command", "")
        problem = problem or rm_problem(cmd) or push_problem(cmd)
    if problem:
        print(f"BLOCKED by scripts/guard.py: {problem}. If the user really wants this, ask them to run it themselves.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
