---
name: evolve
description: "Run one self-improvement generation: scrape self, mine failures and usage, mutate rules/skills, commit. Trigger words: evolve, scrape yourself, self-improve, new generation."
---

# Evolve

One generation = scrape → reflect → mutate → verify → record → commit.

## 1. Scrape
```bash
python3 scripts/doctor.py                                            # baseline fitness + errors (note the metrics)
bash scripts/scrape_self.sh && git diff self/inventory.md            # environment change since last generation
cat memory/failures.log                                              # failed tool calls (hook)
cut -f2 memory/skill-usage.log 2>/dev/null | sort | uniq -c | sort -rn   # skill usage (hook)
```
Every few generations, or when asked, refresh upstream sources (needs the user's go-ahead; it vendors third-party code):
`python3 scripts/import_sources.py --update && git diff --stat`.

## 2. Reflect
Read `memory/learnings.md` and skim this session. Look for:
- **Failures** in the log → each distinct cause is a lesson (or re-scores an existing one).
- **User corrections** this session → highest-value lessons; record every one.
- **Repeated workflows** (3+ times across `EVOLUTION.md`) → `/learn` them into a skill.
- **Dead or overlapping skills** (usage log, > ~30 skills) → `/curate`.
- **Rules that never fired or misfired** in `CLAUDE.md` → reword or prune.
- **Last generation's hypothesis** in `EVOLUTION.md` → did it hold?

## 3. Mutate (at most 3 changes, highest expected value first)
- Lessons: new ones start at 0.5 (0.7 if the user said it). Re-observed +0.1, contradicted −0.2, drop below 0.3.
- Patch a skill (`## Gotchas` or a fixed step), `/learn` a new one, or promote one from the catalog
  (`python3 scripts/catalog.py search …` then `promote`, which needs the user's approval to import).
- Edit a rule in `CLAUDE.md`, or improve a script in `scripts/`.
Never weaken safety, guard, permission, or git rules as a "mutation".

## 4. Verify
Run what you changed: `bash scripts/test_hooks.sh` for hooks/guard, the skill's Verification step for skills.
`python3 scripts/doctor.py` must end `healthy`; compare its metrics with the baseline. A generation that raises
`skill_description_chars` should have earned it.
Then empty the processed logs: `: > memory/failures.log`.

## 5. Record and commit
Append to `EVOLUTION.md`:
```
## Generation N — YYYY-MM-DD
- Environment diff: <one line, or "none">
- Previous hypothesis: <held / failed / untested, with evidence>
- Fitness: <doctor metrics that moved, before → after>
- Mutations: <bullets>
- Hypothesis: <what should be measurably better next time>
```
```bash
git add -A && git commit -m "evolve: generation N — <summary>"
```

## Gotchas
- The inventory is deterministic on purpose: don't add timestamps to it or every diff becomes noise.
- Hook changes in `.claude/settings.json` only take effect in the next session; test hooks by piping JSON into the script.
