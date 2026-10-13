# Learnings

One line each, dated, newest first. Merge or drop stale ones (keep under 60 lines).

- 2026-10-13 — The firecrawl plugin's skills are installed but the `firecrawl` CLI is not on PATH; check `self/inventory.md` before relying on it, fall back to WebFetch/WebSearch or Playwright.
- 2026-10-13 — Playwright MCP is available and Chromium is preinstalled at /opt/pw-browsers; never run `playwright install`.
- 2026-10-13 — Skill frontmatter descriptions can contain escaped quotes (`\"`) and literal `\n`; strip both when parsing them in shell.
- 2026-10-13 — Cloud containers are ephemeral: anything learned must be committed and pushed, or it's lost.
