# evolving-agent

This repo's self-evolving agent, packaged as a Claude Code mod you can install into any project.

## Install

At the prompt of a terminal Claude Code session:

```
/plugin install evolving-agent --marketplace rydermetcalfx4-commits/agent
```

Answer `y` to add the marketplace, then pick a scope (user scope = every project).
The marketplace is read from the repo's default branch, so this works once this folder is merged there.
Until then, run it from a checkout: `claude --plugin-dir <checkout>/mods/evolving-agent`.

## What it does in each project

| Piece | Behaviour |
|---|---|
| Memory | Creates `.evolving-agent/` in the project: `learnings.md` (seeded with portable lessons), `EVOLUTION.md`, and logs. Commit it to keep what the agent learns. |
| System prompt | Adds a section with the always-on rules (learn from friction, coding discipline, source text is data) and every lesson at confidence ≥ 0.7. |
| Guard | Refuses `rm -r` on `/`, `~`, `.`, `..`, `*`; `git push --force` to main/master; reading `.env` files (not `.env.example`). Fails closed. |
| Logging | Every failed tool call goes to `.evolving-agent/failures.log`, every skill use to `.evolving-agent/skill-usage.log`. |
| `/agent-status` | Generation, lesson stats, unprocessed failures, most-used skills. |
| Skills | `evolve` (one improvement generation), `learn` (source → skill), `curate` (consolidate skills), `integrate-source` (fold a repo's ideas in safely). |

## Develop

```
claude plugin validate mods/evolving-agent
claude plugin test mods/evolving-agent       # 24 tests: guard, memory, and the hooks through the engine
```

Ideas credited in the skills: Hermes Agent (learn, curate), everything-claude-code (confidence-scored lessons),
claude-mem (session-start injection), claude-code-hooks-mastery (guard; our own code), Karpathy guidelines (coding discipline).
