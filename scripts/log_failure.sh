#!/usr/bin/env bash
# PostToolUseFailure hook: append one line per failed tool call to memory/failures.log.
# /evolve mines this log for lessons, then clears it. Never blocks the session.
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
LOG="$ROOT/memory/failures.log"
input=$(cat 2>/dev/null || true)
line=$(printf '%s' "$input" | jq -r '
  [ (now | strftime("%Y-%m-%d")),
    (.tool_name // "?"),
    ((.tool_input.command // .tool_input.file_path // .tool_input.url // "") | tostring | .[0:120]),
    ((.error // .tool_response.error // .message // "") | tostring | gsub("\\s+"; " ") | .[0:200])
  ] | join(" | ")' 2>/dev/null) || line="$(date +%F) | unparsed failure"
mkdir -p "$(dirname "$LOG")"
echo "$line" >> "$LOG"
# keep the log bounded
tail -n 200 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG"
exit 0
