---
name: app-automation
description: "Act in external apps (Gmail, Slack, Notion, Jira, Stripe, 800+) via Composio Rube MCP instead of drafting."
---

# App automation (Composio / Rube MCP)

Router over `catalog/composio/` — one playbook per app, imported from ComposioHQ/awesome-claude-skills.
They're kept out of `.claude/skills/` so 800+ descriptions don't bloat every session.

## 1. Find the app's playbook
```bash
ls catalog/composio catalog/composio/skills 2>/dev/null | grep -i '<app>'   # e.g. slack, notion, googlesheets
```
Read `catalog/composio/<app>.md` (or `catalog/composio/skills/<app>.md` after the v2 importer has run). It lists the toolkit's workflows, tool slugs, and known pitfalls.

## 2. Make sure Rube MCP is connected
Check for tools named like `RUBE_SEARCH_TOOLS` (load via ToolSearch with query `rube`).
If missing, tell the user it isn't connected and how to add it — don't add it yourself:
- Claude Code: `claude mcp add --transport http rube https://rube.app/mcp`
- claude.ai / cloud sessions: add `https://rube.app/mcp` as a custom connector.
Rube is a third-party service (Composio); the user authorizes each app through its auth link.

## 3. Run the workflow
1. `RUBE_SEARCH_TOOLS` with the use case → current tool slugs and schemas (schemas change; never guess).
2. `RUBE_MANAGE_CONNECTIONS` with the toolkit → must be ACTIVE; otherwise hand the user the auth link.
3. Execute the tools the playbook describes.
4. Confirm with the user before anything outward-facing (sending email, posting, deleting, paying).

## Gotchas
- Prefer a first-party connector or MCP already in the session (e.g. GitHub MCP) over Rube for the same app.
- Catalog filenames drop the `-automation` suffix and leading dashes (`-2chat-automation` → `2chat.md`).
