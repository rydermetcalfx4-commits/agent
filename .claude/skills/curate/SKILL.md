---
name: curate
description: "Consolidate, archive, and tighten the skill library when it grows past ~30 skills or skills overlap."
---

# Curate

Keep `.claude/skills/` a library of class-level skills, not a pile of one-session micro-skills.
Every skill description is loaded into every session, so dead or duplicate skills cost context and misroute.
Adapted from Hermes Agent's curator (NousResearch/hermes-agent, MIT).

## Inputs
```bash
ls .claude/skills
cut -f2 memory/skill-usage.log | sort | uniq -c | sort -rn     # usage, from the PreToolUse hook
cat .claude/skills/.vendored 2>/dev/null                         # skills owned by scripts/import_sources.py
```

## Rules
1. **Never delete. Archive**: `git mv .claude/skills/<name> .claude/skills-archive/<name>`. Archives are recoverable.
2. **Don't edit vendored skills in place** (listed in `.vendored`); the next import overwrites them. To change one,
   remove it from `sources.json` `promote` and copy it in as our own skill.
3. **Don't archive the core loop**: `evolve`, `learn`, `curate`, `app-automation`.
4. **Usage is weak evidence.** Zero uses isn't a reason to archive unless the skill is >30 days old *and* obsolete or
   absorbed elsewhere. Judge overlap on content.
5. **Consolidate by cluster.** Group skills by shared prefix or domain. Ask "would a maintainer write these as N skills
   or one skill with N sections?" If one: merge into the broadest member (or a new umbrella), distilling each sibling into
   rules ("do X, because Y"), and push depth into the umbrella's `references/`. Moving files unchanged isn't consolidating.
6. **Flag narrow names**: a skill named after one bug, PR, or error string belongs inside an umbrella.
7. **Trim bloated skills**: a SKILL.md over ~500 lines should keep its always-on rules and move detail to `references/`.

## Output
Commit `evolve: curate — N merged, M archived`, and append to the current `EVOLUTION.md` generation:
```yaml
consolidations: [{from: <skill>, into: <umbrella>, reason: <why>}]
archived: [{name: <skill>, reason: <why>}]
```
