---
name: evolve
description: "Scrape the agent's own environment, diff it against the last generation, fold in lessons learned, and commit a new generation. Trigger words: evolve, scrape yourself, self-improve, new generation."
---

# Evolve

One generation = scrape → diff → reflect → mutate → record → commit.

## 1. Scrape
```bash
bash scripts/scrape_self.sh
git diff --stat self/inventory.md
git diff self/inventory.md
```
The diff is the environmental change since the last generation (new tools, plugins, skills, version bumps).

Every few generations (or when asked), also re-scrape upstream sources and review what changed:
```bash
bash scripts/import_sources.sh && git status --short | head -50
```

## 2. Reflect
Read `memory/learnings.md`, `memory/failures.log` (automatic record of failed tool calls), and skim this session's work. Ask:
- What went wrong or took a workaround? → that's a lesson.
- What did I do by hand 3+ times (across `EVOLUTION.md` history)? → that's a missing skill.
- Which rule in `CLAUDE.md` never fired, or misfired? → prune or reword it.
- Did the inventory diff add a capability that changes how I should work? → add a rule.

## 3. Mutate (small, testable changes only)
Pick at most 3 changes, ordered by expected value:
- Add/patch a lesson in `memory/learnings.md` (dated, one line each, keep under 60 lines; merge or drop stale ones).
- Patch a skill in `.claude/skills/` (add a `## Gotchas` entry, or fix a step).
- Create a new skill for a repeated workflow.
- Edit a rule in `CLAUDE.md`.
- Improve `scripts/scrape_self.sh` if the inventory missed something useful.
- Promote a skill from `catalog/external-skills.md` into `.claude/skills/` if a task needed it (add it to `scripts/import_sources.sh` so it stays reproducible).

After folding failures into lessons, empty the log: `: > memory/failures.log`.

Never weaken safety, permission, or git rules in `CLAUDE.md` as a "mutation".

## 4. Record
Append to `EVOLUTION.md`:
```
## Generation N — YYYY-MM-DD
- Environment diff: <one line, or "none">
- Mutations: <bullets>
- Hypothesis: <what should be better next time, so the next generation can check>
```
Then check the previous generation's hypothesis: did it hold? Say so in this entry.

## 5. Commit
```bash
git add -A self memory .claude CLAUDE.md EVOLUTION.md scripts
git commit -m "evolve: generation N"
```

## Gotchas
- The inventory is deterministic on purpose: don't add timestamps to it or every diff becomes noise.
- Fresh repos have no commits yet, so `git diff` shows nothing on generation 1; that's expected.
