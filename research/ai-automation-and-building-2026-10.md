# Using AI to automate and to build things: field guide, 2026-10

A distilled survey: web search, plus primary sources cloned and read (anthropics/claude-cookbooks, best-of-mcp-servers,
awesome-n8n-templates, awesome-ai-agents lists). Blog and vendor comparisons disagree on star counts and prices, so the
numbers below are directional. Primary docs win. The operational version of this guide is the `/automate` skill.

## 1. The core decision: use the lightest mechanism that works
Anthropic's "Building effective agents" guidance, reflected across the cookbook: start with the simplest thing, and add
autonomy only when the task can't be scripted.

| Rung | Use when | Here |
|---|---|---|
| 0. A plain script or cron | Steps are fixed and no judgment is needed | `scripts/`, cron, CI |
| 1. One LLM call in a script | Needs judgment on text (classify, extract, summarise) | Messages API (`claude-api` skill) |
| 2. Workflow: LLM calls on predefined paths | Known stages with judgment inside them | the patterns in §2 |
| 3. No-code automation platform | Glue between SaaS apps, run by non-coders | Zapier, Make, n8n, Activepieces |
| 4. A tool-using agent loop | Steps aren't known in advance | Claude Code + skills/MCP; Agent SDK; `offline/local_agent.py` |
| 5. Multi-agent / orchestrated | Too big for one context window, or verification must be enforced | subagents, dynamic workflows, Managed Agents multiagent |

Higher rungs cost more tokens and are harder to debug. Climb only when the rung below fails a real test case.

## 2. Workflow and agent patterns ([cookbook: patterns/agents](https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents))
- **Prompt chaining**: fixed sequence; check the output between steps ("gates").
- **Routing**: classify the input, then send it to a specialised prompt or model. Easy inputs can go to a cheap model.
- **Parallelization**: split independent parts (sectioning) or run the same task several times and vote.
- **Orchestrator–workers**: a planner splits the work at runtime and workers execute. Best economics: a **frontier model plans
  and synthesizes, cheap models do the token-heavy reading**. The cookbook measured 84–98% of input tokens billed at the worker rate.
- **Evaluator–optimizer**: a generator plus a grader with a written rubric, looping until pass or a cap is hit. The grader works in
  **its own context**, so it can't see the writer's shortcuts (Managed Agents "Outcomes").
- **Advisor**: a cheap working agent consults a stronger model only at hard decision points.
- **Dynamic workflows** (Claude Code `Workflow` tool): Claude writes a JS orchestration script that fans out subagents
  (up to 16 concurrent, 1,000 per run). Use it when the plan should live in code: every item gets the same treatment and verification
  is enforced by structure.

## 3. Context engineering: the main skill in building agents
Context is finite, and recall degrades as it fills ("context rot"). Aim for the smallest set of high-signal tokens.
- **Compaction**: summarise long conversations and continue (first-party in the API).
- **Tool-result clearing**: drop old tool outputs that can be fetched again, but keep the record that the call happened.
- **Memory**: structured notes in external storage, carried across sessions (API memory tool; this repo's `memory/`).
- **Subagents**: isolate exploration in a separate context and return only a summary.
- **Programmatic tool calling**: the model writes code that calls tools and filters big results before they reach the context.
- **Let the model discover context through tools** (search, grep) instead of stuffing everything up front.
- **Agentic search vs. vector RAG**: keyword or grep tool-search reached about 90% of RAG quality in published comparisons, with no index to maintain.
  Vector RAG still wins on huge corpora or fuzzy semantic lookups. Contextual retrieval (cookbook) improves RAG.
  Memory retrieval needs access checks as well as relevance: a memory can be relevant yet belong to another user.

## 4. Cost checklist ([cookbook: cost_optimization](https://github.com/anthropics/claude-cookbooks/tree/main/cost_optimization), in order)
1. Make it work on a capable model, write an eval, and measure a baseline. 2. Prompt caching (stable prefix first).
3. Fewer input tokens: discover context via tools. 4. Agent-loop efficiency: stop context compounding turn over turn.
5. Tighter output constraints. 6. Batch API for anything not interactive (about half price). 7. Only then, a cheaper model or lower effort.

## 5. Verification and evals
- Agents produce things that *look* done. Give every task a check the agent can run: tests, a build, a screenshot diff, a rubric grader.
- Start an eval set with **10–50 real cases written by hand**, and add cases from failures you've actually seen. The dataset matters more than the tool.
- Tools: **promptfoo** (CLI/YAML, local and CI, free) for merge gates; Braintrust, LangSmith or Langfuse for hosted traces and experiments;
  Ragas for RAG. Re-check LLM-as-judge scores against fresh human labels from time to time.
- Observability: OTel GenAI spans (`invoke_agent` / `chat` / `execute_tool`). This repo sends them to Honeycomb; see `observability/`.

## 6. Building software with AI
- **Explore → Plan → Implement → Commit.** Plan mode first. Keep tasks small and reviewable, and give the agent a way to verify each one.
- **Spec-driven development** for anything non-trivial: specify → plan → tasks, with the spec updated in the same PR as the code
  (GitHub Spec Kit, Kiro, cc-sdd; `superpowers` brainstorm/plan/execute is already in the catalog). Skip the ceremony for one-line fixes.
- **App builders**: Lovable (non-coders, React+Supabase), Bolt (choose your framework), v0 (polished React/shadcn UI),
  Replit Agent (build and host), Base44 (all-in-one backend). They get you about 70% of the way; the last 30% needs real code, which is where Claude Code comes in.
- Agent frameworks, when you need your own agent: **Claude Agent SDK** (the Claude Code runtime as a library: tools,
  skills, subagents, hooks), **Claude Managed Agents** (hosted sessions, outcomes, multiagent, budgets), OpenAI Agents SDK,
  LangGraph (stateful graphs, checkpoints, human-in-the-loop), CrewAI (role teams), Pydantic AI. Try plain API calls first.

## 7. Automating work across apps
- **Zapier**: easiest, ~7–8k connectors, gets expensive per task at volume. **Make**: visual branching, cheaper at scale.
  **n8n**: code steps, agent nodes, self-hostable (cheapest at scale if you can run it). **Activepieces**: open-source alternative.
  Agent-first options: Gumloop, Lindy, Relay.app.
- n8n templates: [awesome-n8n-templates](https://github.com/enescingoz/awesome-n8n-templates) (280+, CC BY 4.0) covers
  Gmail, Telegram/WhatsApp bots, Sheets/Drive, Notion, Slack, PDF processing, RAG chatbots, and research agents.
- From Claude directly: first-party connectors and MCP servers, or `/app-automation` (Composio, 800+ apps).
- **Common money-making automations for small businesses**: speed-to-lead (reply to new leads in minutes), invoice chasing,
  review requests, appointment reminders, inbox triage, CRM hygiene, weekly KPI digests, and win-back campaigns
  (see the `small-business` plugin and `/make-money`).

## 8. MCP servers worth knowing (from [best-of-mcp-servers](https://github.com/tolkonepiu/best-of-mcp-servers), 404 ranked)
- Docs and code: **Context7** (current library docs), **Serena** (symbolic code navigation), codebase-memory-mcp, GitMCP (any GitHub repo).
- Browser: **Playwright MCP** (deterministic, DOM-based, already installed here), Skyvern (vision-based), UI-TARS, BrowserMCP (your own Chrome).
- Files and data: **MarkItDown** (any file → markdown), MindsDB / Google genai-toolbox (databases), Baserow, Filestash.
- Platforms: **GitHub**, AWS (awslabs/mcp), **Pipedream** (2,500 APIs), **Apify** (3,000+ scrapers), Figma-Context.
- Memory and context: cognee (graph/vector memory), headroom (compresses tool output).
- Building your own: **FastMCP** (Python) or the TS SDK, guided by the `mcp-builder` skill.
- Security: MCP servers run with your credentials. Prefer official or high-quality-score servers, read the code of small ones, and give each one the narrowest token you can.

## 9. Browser and computer use
- DOM-driven (Playwright MCP, Stagehand `act/extract/observe`, Browser Use in Python) is precise but breaks when selectors change.
- Vision-driven computer use (Claude computer use, Operator, Skyvern) handles canvas, PDFs and odd UIs, but is slower and costs more. Production systems often combine both.
- Cloud browsers (Browserbase and others) handle sessions, proxies and stealth. Respect each site's terms and robots rules, and never automate logins you don't own.

## 10. Voice agents
**Pipecat** (Python, most integrations) and **LiveKit Agents** (WebRTC, telephony, scale) lead the open-source options. Check licences:
LiveKit's turn-detection models have their own terms. ElevenLabs + Claude is a low-latency recipe in the cookbook. Phone automation
(booking, qualification, reminders) is a common small-business service.

## 11. Where to go deeper
- [anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks) (MIT, 97 recipes; index in `catalog/external/claude-cookbooks.md`)
- Anthropic engineering posts: "Building effective agents", "Effective context engineering for AI agents"
- Agent lists: [caramaschiHG/awesome-ai-agents-2026](https://github.com/caramaschiHG/awesome-ai-agents-2026) (CC0),
  [500-AI-Agents-Projects](https://github.com/ashishpatel26/500-AI-Agents-Projects) (MIT, use cases by industry),
  [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) (MIT)
