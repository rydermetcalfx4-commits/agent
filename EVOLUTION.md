# Evolution log

## Generation 1 — 2026-10-13
- Environment diff: first scrape (baseline). Claude Code 2.1.296; plugins: adaptive-agent, firecrawl, playwright.
- Mutations:
  - Created `scripts/scrape_self.sh` (self-inventory), `/evolve` skill, `CLAUDE.md` rules, `memory/learnings.md`.
  - SessionStart hook re-scrapes the inventory so each session starts with a current self-model.
  - Fixed the scraper's handling of escaped quotes in skill descriptions (found on first run).
- Hypothesis: next session, the inventory diff will show any plugin/tool changes without manual checking, and the firecrawl-CLI lesson will avoid one failed command.

## Generation 2 — 2026-10-13
- Environment diff: +25 project skills, +832 catalog playbooks, inventory now tracks a HolyClaude-sized toolset (and what's missing from it).
- Previous hypothesis: untested yet (no new session has started since gen 1).
- Mutations:
  - Scraped ComposioHQ/awesome-claude-skills: 24 standalone skills → `.claude/skills/`; 832 Composio app playbooks → `catalog/composio/` behind a new `/app-automation` router; external skill index → `catalog/external-skills.md`.
  - Scraped CoderLuii/HolyClaude: `holyclaude/docker-compose.yaml` to run this repo in it, its environment notes, and its Apprise `notify.py` wired to Stop/PostToolUseFailure hooks (off unless `~/.claude/notify-on` exists).
  - New PostToolUseFailure hook writes `memory/failures.log`, so "learn from friction" no longer depends on me remembering.
  - `scripts/import_sources.sh` makes the whole import reproducible; `/evolve` now re-runs it periodically.
- Hypothesis: next `/evolve` will find at least one real entry in `memory/failures.log` and turn it into a lesson without the user pointing it out.
