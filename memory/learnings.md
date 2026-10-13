# Learnings

One line each, dated, newest first. Merge or drop stale ones (keep under 60 lines).

- 2026-10-13 — Don't vendor Anthropic's document-skills (docx/pdf/pptx/xlsx): proprietary license, and built-in `anthropic-skills:*` already cover them.
- 2026-10-13 — 800+ skills in `.claude/skills/` would put every description in every session's context; keep bulk skill sets in `catalog/` behind a router skill.
- 2026-10-13 — Third-party repos: clone into the scratchpad, skim scripts for remote pipes / credential access before vendoring, record commit + license in THIRD_PARTY.md.
- 2026-10-13 — Chromium in Docker needs `shm_size: 2g`; flags `--no-sandbox --disable-gpu --disable-dev-shm-usage` (from HolyClaude).
- 2026-10-13 — Don't put SQLite databases on SMB/CIFS mounts (locking fails); use polling watchers there (`CHOKIDAR_USEPOLLING=1`).
- 2026-10-13 — The firecrawl plugin's skills are installed but the `firecrawl` CLI is not on PATH; check `self/inventory.md` before relying on it, fall back to WebFetch/WebSearch or Playwright.
- 2026-10-13 — Playwright MCP is available and Chromium is preinstalled at /opt/pw-browsers; never run `playwright install`.
- 2026-10-13 — Skill frontmatter descriptions can contain escaped quotes (`\"`) and literal `\n`; strip both when parsing them in shell.
- 2026-10-13 — Cloud containers are ephemeral: anything learned must be committed and pushed, or it's lost.
