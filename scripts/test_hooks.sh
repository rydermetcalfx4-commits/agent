#!/usr/bin/env bash
# Regression tests for the hook scripts. Run after changing anything in scripts/ that a hook calls.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
fail=0
expect() { # expected_exit json
  printf '%s' "$2" | python3 "$ROOT/scripts/guard.py" 2>/dev/null; got=$?
  if [ "$got" != "$1" ]; then echo "FAIL guard (want $1, got $got): $2"; fail=1; fi
}
# blocked
expect 2 '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}'
expect 2 '{"tool_name":"Bash","tool_input":{"command":"cd x && rm -fr ~"}}'
expect 2 '{"tool_name":"Bash","tool_input":{"command":"rm -r -f ."}}'
expect 2 '{"tool_name":"Bash","tool_input":{"command":"rm -rf $HOME"}}'
expect 2 '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}'
expect 2 '{"tool_name":"Read","tool_input":{"file_path":"/app/.env"}}'
expect 2 '{"tool_name":"Bash","tool_input":{"command":"cat .env.production"}}'
# allowed
expect 0 '{"tool_name":"Bash","tool_input":{"command":"rm -rf build/ dist"}}'
expect 0 '{"tool_name":"Bash","tool_input":{"command":"rm -rf ./node_modules foo.txt"}}'
expect 0 '{"tool_name":"Bash","tool_input":{"command":"git push --force-with-lease origin main"}}'
expect 0 '{"tool_name":"Bash","tool_input":{"command":"git push -u origin claude/x"}}'
expect 0 '{"tool_name":"Read","tool_input":{"file_path":"/app/.env.example"}}'
expect 0 '{"tool_name":"Bash","tool_input":{"command":"grep -r dotenv src/"}}'
expect 0 '{"tool_name":"Read","tool_input":{"file_path":"/app/src/environment.ts"}}'
expect 0 'not json'
# regression: prose mentioning .env / force-push inside heredocs or messages must not trip the guard
expect 0 '{"tool_name":"Bash","tool_input":{"command":"cat >> EVOLUTION.md <<'"'"'EOF'"'"'\n- guard blocks `.env` reads\nEOF\ngit commit -m \"blocks git push --force main\""}}'
expect 0 '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"cat .env is blocked\""}}'
expect 2 '{"tool_name":"Bash","tool_input":{"command":"echo hi && head -5 config/.env"}}'
expect 2 '{"tool_name":"Bash","tool_input":{"command":"git push -f origin HEAD:main"}}'

# failure logger: one line per failure, newlines collapsed
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"a\nb"},"error":"x\ny"}' | CLAUDE_PROJECT_DIR="$TMP" bash "$ROOT/scripts/log_failure.sh"
[ "$(wc -l < "$TMP/memory/failures.log")" = 1 ] && grep -q '| Bash | a b | x y$' "$TMP/memory/failures.log" || { echo "FAIL log_failure: $(cat "$TMP/memory/failures.log")"; fail=1; }

# skill tracker
echo '{"tool_input":{"skill":"evolve"}}' | CLAUDE_PROJECT_DIR="$TMP" bash "$ROOT/scripts/track_skill.sh"
grep -q $'\tevolve$' "$TMP/memory/skill-usage.log" || { echo "FAIL track_skill"; fail=1; }

# settings.json is valid JSON and every hook script exists
jq -e . "$ROOT/.claude/settings.json" >/dev/null || { echo "FAIL settings.json"; fail=1; }
for s in $(grep -o 'scripts/[a-z_]*\.\(sh\|py\)' "$ROOT/.claude/settings.json" | sort -u); do
  [ -f "$ROOT/$s" ] || { echo "FAIL missing $s"; fail=1; }
done

[ $fail = 0 ] && echo "all hook tests passed"
exit $fail
