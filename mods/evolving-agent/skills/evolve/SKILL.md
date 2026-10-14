---
name: evolve
description: "Run one self-improvement generation: mine failures and usage, update lessons and skills, record and commit."
---

# Evolve

One generation = observe → reflect → mutate → verify → record. Memory lives in `.evolving-agent/` in the project.

## 1. Observe
Run `/agent-status`, then read:
- `.evolving-agent/failures.log`: every failed tool call, logged by the plugin
- `.evolving-agent/skill-usage.log`: every skill invocation
- `.evolving-agent/learnings.md`, and this session's conversation (corrections from the user count most)
- the last generation in `.evolving-agent/EVOLUTION.md`, and its hypothesis

## 2. Reflect
- Each distinct failure cause → a new lesson, or re-score an existing one.
- Each user correction → a lesson at 0.7 or higher.
- A workflow done 3+ times (check EVOLUTION.md history) → the learn skill.
- More than ~30 project skills, or overlapping ones → the curate skill.
- Did last generation's hypothesis hold? Say so with evidence.

## 3. Mutate (at most 3 changes, highest value first)
Lessons (new 0.5, user-stated 0.7, re-observed +0.1, contradicted −0.2, drop below 0.3, max 60 lines),
a `## Gotchas` entry in a project skill, a new skill, or a rule in the project's CLAUDE.md.
Never weaken safety rules or the plugin's guard as a "mutation".

## 4. Verify
Re-run whatever the change affects. Then empty the processed log: write an empty `.evolving-agent/failures.log`.

## 5. Record
Append to `.evolving-agent/EVOLUTION.md`:
```
## Generation N — YYYY-MM-DD
- Previous hypothesis: <held / failed / untested, with evidence>
- Mutations: <bullets>
- Hypothesis: <what should be measurably better next time>
```
If the project is a git repo, commit with a message starting `evolve:`.
