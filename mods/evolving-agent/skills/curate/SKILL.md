---
name: curate
description: "Consolidate and archive project skills when they pass ~30 or overlap; keeps per-session context small."
---

# Curate

Keep `.claude/skills/` a library of class-level skills. Every description loads into every session.
Adapted from Hermes Agent's curator (NousResearch/hermes-agent, MIT).

Inputs: the skill list, and usage from `.evolving-agent/skill-usage.log` (count per skill).

Rules:
1. Never delete; archive to `.claude/skills-archive/<name>` (with `git mv` in a git repo).
2. Usage is weak evidence: archive a zero-use skill only if it is >30 days old and obsolete or absorbed.
3. Consolidate by cluster: "would a maintainer write these as N skills or one with N sections?" If one, merge into the
   broadest, distilling each sibling into rules ("do X, because Y"), with depth in `references/`.
4. A skill named after one bug, PR, or error string belongs inside an umbrella.
5. A SKILL.md over ~500 lines keeps its always-on rules and moves detail to `references/`.

Record the result in the current generation of `.evolving-agent/EVOLUTION.md`:
`consolidations: [{from, into, reason}]`, `archived: [{name, reason}]`.
