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

## Generation 3 — 2026-10-14
- Environment diff: +3 core skills (`learn`, `curate`, rewritten `evolve`), +4 hook scripts; the inventory now reports agents and the catalog index.
- Previous hypothesis: **held.** The PostToolUseFailure hook logged 4 real failures this session without prompting. They became lessons
  (GitHub search blocked, egress-blocked sites, newline-corrupted logs), and the last one exposed and fixed a bug in the logger itself.
- Source: scraped "claude tools" on GitHub. Search itself is blocked here, so I used web search plus 13 cloned repos (see `research/claude-tools-2026-10.md`).
- Mutations:
  - `/learn` (Hermes authoring standards) and `/curate` (Hermes curator: class-level umbrellas, archive-never-delete).
  - Confidence-scored lessons (ECC instincts); SessionStart now injects lessons ≥ 0.7 into context (claude-mem idea).
  - `scripts/guard.py` PreToolUse guard: catastrophic `rm -r`, force-push to main, secrets-file reads (hooks-mastery idea, own code).
    It went live mid-session and false-positived on this very commit; fixed to parse per command, regression test added.
  - Skill-usage tracking hook feeding `/curate`; `scripts/test_hooks.sh` regression suite (21 guard cases + logger + tracker).
  - Coding-discipline rules in `CLAUDE.md` (Karpathy guidelines).
  - `sources.json` + `scripts/import_sources.py` + `scripts/catalog.py`: 15 sources, ~2,500 skills/agents/commands as a searchable
    catalog plus 17 promoted skills. **Written and parser-tested, not yet run**: running it vendors third-party code and needs the user's approval.
- Hypothesis: next session, the injected lessons prevent at least one repeat of a logged failure (e.g. no attempt at GitHub search),
  and `memory/skill-usage.log` gets its first real entries.
