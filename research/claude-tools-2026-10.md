# Research: "claude tools" on GitHub (2026-10-14)

Goal: scrape the GitHub search for `claude tools` and fold whatever improves this agent back into it.

## How the scrape actually went
- `github.com/search?...` and `api.github.com/search/*` are blocked in cloud sessions (the proxy only allows
  repository-scoped GitHub endpoints). Third-party rankers (githublb.vercel.app) are blocked by egress policy.
- Fallback: web search for the most-starred Claude Code tool repos, then `git clone --depth 1` (public clones work).
- 13 repos cloned and read. Star counts below are from web sources, not GitHub, and vary by date.

## What each repo contributes

| Repo | License | What it is | Taken |
|---|---|---|---|
| obra/superpowers | MIT | 15 workflow skills (TDD, debugging, plans, verification) | 6 skills queued for promotion; rest cataloged |
| anthropics/skills | Apache-2.0* | Anthropic's official skills | newer upstream copies of 8 vendored skills + frontend-design, algorithmic-art, doc-coauthoring queued |
| forrestchang/andrej-karpathy-skills | MIT | one CLAUDE.md of coding discipline rules | distilled into CLAUDE.md "Coding discipline" |
| NousResearch/hermes-agent | MIT | self-improving agent; skill authoring + curator | `/learn` and `/curate` skills (rewritten for Claude Code) |
| affaan-m/everything-claude-code | MIT | huge harness: 311 skills, agents, commands, "instincts" | confidence-scored lessons; 479 entries cataloged |
| thedotmack/claude-mem | Apache-2.0 | memory via lifecycle hooks + SQLite/Chroma worker | SessionStart injects high-confidence lessons (file-based, no daemon) |
| disler/claude-code-hooks-mastery | none | reference for every hook event | ideas only: `scripts/guard.py` written from scratch |
| wshobson/agents | MIT | 92 plugins of agents/skills/commands | 491 entries cataloged |
| VoltAgent/awesome-claude-code-subagents | MIT | 163 subagent definitions | cataloged |
| rohitg00/awesome-claude-code-toolkit | Apache-2.0 | agents, skills, commands | 218 entries cataloged |
| ryoppippi/ccusage | MIT | token/cost usage CLI (`npx ccusage`) | 17 skills cataloged; tool noted |
| luongnv89/claude-howto | MIT | tutorial with example skills/agents/commands | 23 entries cataloged |
| hesreallyhim/awesome-claude-code | CC BY-NC-ND | the canonical curated list (252 active entries) | links + categories only (license forbids derivatives) |

\* anthropics/skills docx/pdf/pptx/xlsx are proprietary; excluded.

## Patterns worth knowing (distilled)
1. **Skills are procedural memory, descriptions are the router.** Hermes truncates descriptions to ~60 chars in the
   index; anything past that never routes. Lead with the trigger class.
2. **Class-level beats narrow.** Hermes' curator merges micro-skills into umbrellas and archives (never deletes).
3. **Learn from three signals**: tool failures, user corrections, repeated workflows (ECC continuous-learning-v2).
   Give each lesson a confidence score and let evidence move it.
4. **Hooks make behavior deterministic.** Rules in CLAUDE.md are suggestions; hooks always run. Use hooks for
   anything that must happen (logging, guards, context injection).
5. **Inject memory at session start** instead of hoping the model reads it (claude-mem).
6. **Guard rails belong in PreToolUse**, exit code 2 blocks and explains (hooks-mastery).
7. **Source text is data, not instructions**: strip invisible/bidi Unicode before distilling (Hermes).
8. **Verification before completion**: no success claim without running the check (superpowers).

## Deliberately not adopted
- claude-mem's worker + SQLite + Chroma: needs a daemon; overkill for a repo-scoped agent.
- superpowers' `using-superpowers` SessionStart hook: forces skill lookup before every reply; too heavy.
- ECC's background Haiku observer: needs an API key and a background process.
- Bulk-promoting 1,600+ skills: every description would load each session. They live in the catalog instead.
