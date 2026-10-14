# Using Claude to make money and run a business: GitHub scrape, 2026-10

Scope: repos about *using* Claude (business workflows, marketing, sales, making money), not Claude Code tooling,
which `research/claude-tools-2026-10.md` already covers. GitHub search is blocked in cloud sessions, so repos came from
web search and were cloned at depth 1 into the scratchpad. Income claims in these repos are self-reported and unverified.

## Repos surveyed

| Repo | What it is | License | Use here |
|---|---|---|---|
| [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) | Official role plugins (sales, marketing, finance, small-business, legal, data …), ~250 skills | Apache-2.0 | Install as plugins; catalog (pending approval) |
| [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | 50 marketing skills (offers, pricing, cold email, CRO, SEO, launch) | MIT | Catalog (pending approval) |
| [Sudhakaran88/solopreneur-skills](https://github.com/Sudhakaran88/solopreneur-skills) | 42 growth skills for one-person SaaS/ecom | MIT | Catalog (pending approval) |
| [ognjengt/founder-skills](https://github.com/ognjengt/founder-skills) | 15 founder skills (GTM, pricing, outreach, PRD, SOPs) | MIT | Catalog (pending approval) |
| [OneWave-AI/claude-skills](https://github.com/OneWave-AI/claude-skills) | 229 business/engineering skills (proposals, lead scoring, invoice chasing …) | MIT | Catalog (pending approval) |
| [rdmgator12/awesome-claude-plugins](https://github.com/rdmgator12/awesome-claude-plugins) | Directory of ~333 plugins in Anthropic's catalog | CC0-1.0 | External link index (pending approval) |
| [iamzifei/show-me-the-money](https://github.com/iamzifei/show-me-the-money) | 25-skill "idea to revenue" suite for solo founders | CC BY-NC 4.0 | Ideas only; personal-use plugin install is allowed |
| [garylab/MakeMoneyWithAI](https://github.com/garylab/MakeMoneyWithAI) | List of open-source AI projects for income | none | Ideas only (link) |
| [langgptai/awesome-claude-prompts](https://github.com/langgptai/awesome-claude-prompts) | Prompt collection | none | Ideas only (link) |
| [BrianRWagner/ai-marketing-claude-code-skills](https://github.com/BrianRWagner/ai-marketing-claude-code-skills) | 23 marketing frameworks | none | Ideas only (link) |

## Mechanisms worth having

| Idea | Seen in | Adopted? |
|---|---|---|
| One business-context doc that every skill reads first, so you're not re-asked | marketingskills (`.agents/product-marketing.md`), founder-skills (`FOUNDER_CONTEXT.md`), solopreneur-context | **Yes**: `/make-money` writes `.agents/product-marketing.md`, the same path marketingskills reads |
| A staged pipeline: discover → validate → offer → build → acquire → operate → review | show-me-the-money | **Yes**, as our own stages in `/make-money` (no text copied) |
| Validate before building: cheapest test first, with kill criteria written up front | show-me-the-money ("content MVP ladder"), marketingskills `launch` | **Yes**: a stage-2 rule |
| "Sell real": never fabricate cases, numbers, or reviews | show-me-the-money | **Yes**: a hard rule in `/make-money` |
| The offer matters more than the copy (value, guarantee, scope) | marketingskills `offers` | **Yes**: stage 3; routes to the catalog skill |
| Cross-session state (save/restore decisions) | show-me-the-money | **Yes**, via this repo's existing pattern: a dated log in the context doc |
| Persona review panel (investor, customer, skeptic) | show-me-the-money, marketingskills `marketing-council` | Partly: stage 6 asks for a skeptic pass; no separate skill |
| 24/7 autonomous ops agents | show-me-the-money | **No**: needs always-on infra and credentials, and is risky without review |
| Bulk-promote 50+ marketing skills into `.claude/skills` | all | **No**: catalog instead (each description costs context every session) |

## Money models that actually fit Claude (no income figures; those vary wildly)
1. **Freelance services, delivered faster**: writing, editing, code, data cleanup, research. Disclose AI use where a platform requires it.
2. **Productized services**: a fixed scope and price, e.g. "SEO + CRO audit in 48 h", backed by audit skills.
3. **Automation for small businesses**: connect their tools (CRM, invoices, follow-ups) with `/app-automation` or MCP connectors.
4. **Digital products**: templates, skill packs, guides, Notion or Sheets systems.
5. **Micro-SaaS or tools** built with Claude Code.
6. **Content or audience**: newsletter, YouTube, courses, monetized later.
7. **Ecommerce**: see the built-in `anthropic-skills:dropship-launch`.
8. **Getting hired**: `tailored-resume-generator`, plus interview prep.
