---
name: automate
description: "Use when asked to automate a task or build an AI tool/agent: pick the lightest mechanism, then build it with a check."
---

# Automate or build with AI

Turns "automate X" or "build an AI thing that does Y" into the simplest working mechanism, with a test.
Background and sources: `research/ai-automation-and-building-2026-10.md`. Recipes: `catalog/external/claude-cookbooks.md`.

## Procedure
1. **Pin down the job.** Trigger (schedule, event, on demand), inputs, output, who sees it, how often, what counts as wrong,
   and which accounts it touches. Write 3–5 real example inputs with the expected outputs; these become the check.
2. **Pick the lowest rung that handles every example** (climb only after a failed attempt):
   | Rung | Signal | Build with |
   |---|---|---|
   | Script / cron | fixed steps, no judgment | Python/bash in `scripts/`, cron or CI |
   | One LLM call | judgment on text: classify, extract, summarise, draft | `claude-api` skill (Messages API, structured output) |
   | Workflow | known stages with judgment inside | chaining / routing / parallel / evaluator-optimizer (cookbook `patterns/agents`) |
   | App-to-app glue | SaaS triggers and actions, run by non-coders | first-party connector, `/app-automation`, or n8n/Make/Zapier |
   | Agent loop | steps unknown in advance; needs tools | a Claude Code skill (+ MCP), the Agent SDK, or `offline/local_agent.py` for local models |
   | Orchestrated agents | won't fit one context, or verification must be enforced | subagents / dynamic workflows; plan big, execute small |
   | Repeated in Claude Code itself | "every time X, do Y" | a hook (`update-config` skill) or a skill via `/learn` |
3. **Reuse before building.** Search `.claude/skills/`, `python3 scripts/catalog.py search "<task>"`, `catalog/external/`,
   and the connectors and plugins in `self/inventory.md`. An MCP server probably exists already (best-of-mcp-servers); a missing one
   gets built with `mcp-builder`.
4. **Build the smallest version** that passes the step-1 examples. Defaults:
   - Context: let the model fetch what it needs via tools; cache the stable prompt prefix; batch anything non-interactive.
   - Models: the strongest model plans and judges; cheaper models do bulk reading and extraction.
   - Outputs: structured (JSON/tool schema) whenever code consumes them.
   - Secrets: from env vars or the secrets store, never in the repo (the guard blocks `.env` access).
5. **Verify.** Run the examples. For fuzzy outputs, use a written rubric graded in a separate context (an evaluator).
   Add every observed failure as a new example. No success claim without the run.
6. **Make it observable and safe to run unattended**: log failures (this repo: `memory/failures.log`, OTel to Honeycomb via
   `observability/`), set spend and iteration caps, keep a human approval before sending, paying, deleting, or posting publicly.
7. **Ship it**: commit, with a usage line in the relevant README. If it's a reusable workflow, `/learn` it into a skill.

## Gotchas
- An agent is rarely the answer to a fixed process: a cron job plus one LLM call is cheaper, faster, and debuggable.
- Browser automation (Playwright MCP is installed) breaks on UI changes; prefer an API or connector when one exists.
- No-code platforms bill per task or operation, so estimate volume × price before choosing one; n8n self-hosted is cheapest at scale.
- Scraping and automation must respect site terms and rate limits, and must not use accounts the user doesn't own.
