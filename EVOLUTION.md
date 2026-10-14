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

## Generation 4 — 2026-10-14
- Environment diff: +1 skill (`integrate-source`), +1 script (`scripts/doctor.py`).
- Previous hypothesis: untested (no new session since gen 3).
- Fitness (doctor, first measurement): 29 skills (5 own, 24 vendored), 6,420 description chars loaded per session,
  15 lessons (12 injected, mean confidence 0.75), 0 unprocessed failures, healthy.
- Mutations:
  - Asked to "do whatever will make you grow". The import of third-party skills was blocked a second time by the auto-mode
    classifier (a vague go-ahead isn't approval of a specific import), so it stays pending; that lesson is now at confidence 1.0.
  - `/learn` applied to my own history: "scrape a source and integrate it" ran 3 times (gens 2–3), so it became the `integrate-source` skill.
  - `scripts/doctor.py`: a fitness function for evolution (context cost, lesson health, dangling references, hook integrity).
    `/evolve` now measures before and after. Its first run found 1 error and 4 warnings, all fixed.
- Hypothesis: `skill_description_chars` falls in a future generation. Of the 24 bulk-imported skills, those still at zero uses in
  `memory/skill-usage.log` after 2026-11-13 qualify for `/curate` archiving under its 30-day rule.

## Generation 5 — 2026-10-14
- Environment diff: +`mods/evolving-agent` (installable mod), +`.claude-plugin/marketplace.json`.
- Previous hypothesis: untested (still within the same session; the November curate check hasn't come due).
- Fitness: doctor healthy; the mod has 24/24 tests passing, validates, and type-checks.
- Mutations:
  - Cloned the agent into a mod so it can live in any project, not just this repo. The bash/python hooks became one TypeScript module:
    session start seeds `.evolving-agent/` memory, `prompt.compose` injects rules and lessons ≥ 0.7, a single `tool.call`
    hook guards (fails closed) then logs failures and skill use, and `/agent-status` reports fitness.
  - Skills `evolve`, `learn`, `curate`, `integrate-source` rewritten to be project-agnostic (no repo scripts needed).
  - Portable lessons seeded into the mod's template; repo-specific ones left behind.
- Hypothesis: installed in a second project, the mod produces a non-empty `.evolving-agent/failures.log` within its first real
  session, and that project's first `/evolve` turns it into a lesson.

## Generation 6 — 2026-10-14
- Environment diff: +`offline/` (guide, `local_agent.py`, 6 tests), +`catalog/external/ai-projects.md`, +`research/offline-ai-2026-10.md`.
- Previous hypothesis (gen 5, the mod in a second project): untested. But the mod did load in this repo, seeded `.evolving-agent/`,
  and the repo's own skill-usage hook logged real entries, confirming the second half of gen 3's hypothesis.
- Source: scraped AMAI-GmbH/AI-Expert-Roadmap, Lightning-AI/pytorch-lightning, and the 500-AI-projects list (via `integrate-source`),
  then researched offline agents. ollama.com was blocked, so claims were verified against Ollama's own repo docs instead.
- Mutations:
  - `offline/local_agent.py`: a from-scratch agent loop for local models that shares this repo's lessons, guard, and failure log,
    so mistakes made offline feed `/evolve` too.
  - Guide with three levels (Claude Code on Ollama → own loop → own model) and a learning path through nanoGPT,
    LLMs-from-scratch, the Lightning LM example, and nanochat.
  - 2 lessons: model weights are unreachable here (test with fakes); a project's own repo is a fallback for blocked docs sites.
- Hypothesis: when the user runs `local_agent.py` on a real local model, its first failures land in `memory/failures.log`
  and the next `/evolve` turns at least one into a lesson specific to local models.
