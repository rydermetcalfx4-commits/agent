#!/usr/bin/env bash
# PreToolUse hook (matcher: Skill): append "date<TAB>skill" to memory/skill-usage.log.
# /curate uses this to tell living skills from dead weight. Never blocks.
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
skill=$(jq -r '.tool_input.skill // empty' 2>/dev/null)
[ -n "$skill" ] && printf '%s\t%s\n' "$(date +%F)" "$skill" >> "$ROOT/memory/skill-usage.log"
exit 0
