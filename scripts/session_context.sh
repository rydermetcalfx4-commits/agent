#!/usr/bin/env bash
# SessionStart hook. Stdout is added to Claude's context, so keep it short.
# 1. refresh the self-inventory  2. inject high-confidence lessons  3. nudge /evolve when there's input for it
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT" || exit 0
bash scripts/scrape_self.sh >/dev/null 2>&1

# lessons are "- [0.8] YYYY-MM-DD — text"; inject those at >= 0.7 (idea: claude-mem context injection, ECC instinct confidence)
lessons=$(grep -E '^- \[(0\.[7-9]|1\.0)\]' memory/learnings.md 2>/dev/null)
if [ -n "$lessons" ]; then
  echo "High-confidence lessons from memory/learnings.md (apply them):"
  echo "$lessons"
fi
git diff --quiet -- self/inventory.md 2>/dev/null || echo "self/inventory.md changed since last generation; consider /evolve."
[ -s memory/failures.log ] && echo "memory/failures.log has $(wc -l < memory/failures.log) unprocessed failures; consider /evolve."
exit 0
