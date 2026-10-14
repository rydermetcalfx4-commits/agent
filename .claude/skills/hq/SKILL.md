---
name: hq
description: "Use when the user says hq, menu, start, 'what should I do', or 'what can you do': a status check plus the best next moves."
---

# HQ

The user's home screen. They work from the Claude app, give big open goals, and want me to drive. Produce one short,
phone-sized answer: where things stand, then 3–5 concrete next moves they can pick with one word.

## Gather (quietly, in parallel; skip anything that fails)
- **Money**: `ArtifactData list` on `ventures`, `deals`, `income` at https://claude.ai/artifact/W5hQvKFsksev2nc718J8kD.
  Note the month's income, open deals, and any venture whose `next` step looks stale.
- **Agent health**: `python3 scripts/doctor.py | tail -3`; new lines in `memory/failures.log`; `git log --oneline -5`.
- **Pending decisions**: look in `research/*.md` for "pending approval" items (catalog imports, plugins, boards) that are
  still open, and in `sources.json` for sources whose catalog hasn't been imported (`catalog/INDEX.tsv` missing or lacking them).
- **What's possible**: the skills in `.claude/skills/` (one line each from `description`) and the plugins in `self/inventory.md`.

## Answer format
1. **Status**: at most 4 lines (money this month and open deals; agent health; anything waiting on them).
2. **Next moves**: a numbered list, 3–5 items, ranked by value to the user. Each item is one line: what I'd do and the
   skill or tool behind it. Prefer moves that earn money or unblock work. Typical candidates:
   - advance the venture closest to income (`/make-money`, the stage it's in)
   - follow up on deals that are contacted or replied
   - decide a pending approval (say exactly what approving does)
   - automate something they keep doing by hand (`/automate`)
   - learn or research a topic they mentioned (`/integrate-source`, research notes)
   - run `/evolve` if there are unprocessed failures or lessons
3. End with: "Reply with a number, or tell me what you want."

## Rules
- No walls of text: the user reads this on a phone. No headings deeper than bold labels.
- Never invent figures. If a source can't be read, say "couldn't check X" in one line.
- If everything is empty (a new user), lead with `/make-money` stage 1 and a 2-minute question set.
