# Learnings

Format: `- [confidence] YYYY-MM-DD — lesson`. Confidence 0.3 tentative … 0.9 near-certain.
Re-observed → +0.1; contradicted → −0.2; below 0.3 → drop. Lessons at ≥ 0.7 are injected at session start.
Keep under 60 lines; merge or drop stale ones. (Confidence model from ECC continuous-learning-v2.)

- [0.5] 2026-10-14 — The SessionStart inventory scrape can run before synced plugins land, leaving the plugin sections empty; rerun `scripts/scrape_self.sh` before committing self/inventory.md.
- [0.5] 2026-10-14 — Plugin-declared remote MCP servers (e.g. Honeycomb) can fail with a proxy 403 in cloud sessions while the same service's claude.ai connector (`mcp__Honeycomb__*`) works; use the connector. A user-scope `claude plugin install` dies with the container.
- [0.8] 2026-10-14 — User correction: a one-word skill answer ("stocks") meant interest, not experience; I built a plan on it. In /make-money stage 1, ask the experience level before choosing a model.
- [0.6] 2026-10-14 — For knowledge gathering, web-search comparison pages contradict each other (stars, prices); clone the primary repo instead. anthropics/claude-cookbooks `registry.yaml` indexes every recipe.
- [0.6] 2026-10-14 — Model weights can't be fetched in cloud sessions (huggingface.co, ollama.com, GitHub releases blocked; PyPI works). Test model-facing code against a scripted fake server instead.
- [0.7] 2026-10-14 — Mod API: one unmatched hook per event (merge guard + logger), `$` op hooks answer `{ value }` / `{ deny }`, the engine passes absolute paths, and the test `$` takes full event inputs. Validate, tsc, and `claude plugin test` before shipping.
- [0.7] 2026-10-14 — Run `python3 scripts/doctor.py` after any change to skills, lessons, or hooks; it caught a dangling reference in a brand-new skill.
- [0.8] 2026-10-14 — Guards must parse commands per segment and skip heredocs/messages; grepping the whole string blocked my own commit (prose mentioned `.env`). Hook edits to .claude/settings.json can take effect mid-session.
- [0.9] 2026-10-14 — GitHub search (web and API) is blocked in cloud sessions; discover repos via WebSearch, then `git clone --depth 1` (public clones work).
- [0.9] 2026-10-14 — Egress policy blocks many third-party sites (githublb.vercel.app, ollama.com); a project's own GitHub repo usually clones and carries its docs; when WebFetch/curl gets 403 or ENOTFOUND, switch sources, don't retry.
- [1.0] 2026-10-14 — Vendoring third-party skill dirs into .claude/skills is blocked by the auto-mode classifier even after a vague "do whatever"; it needs explicit approval of that specific import (or a user permission rule). Re-observed twice.
- [0.8] 2026-10-14 — Hook logs must collapse newlines in every field (command and error), or multi-line commands corrupt one-line logs.
- [0.7] 2026-10-14 — Skill descriptions route on their first ~60 chars; lead with when-to-use.
- [0.7] 2026-10-13 — Don't vendor Anthropic's docx/pdf/pptx/xlsx skills: proprietary license, and built-in `anthropic-skills:*` cover them.
- [0.8] 2026-10-13 — Bulk skill sets go in `catalog/` behind search (`scripts/catalog.py`), not `.claude/skills/`: every skill description loads every session.
- [0.8] 2026-10-13 — Third-party repos: clone into the scratchpad, read scripts before vendoring, check the license (no license = ideas only), record commit in sources.lock.
- [0.6] 2026-10-13 — Chromium in Docker needs `shm_size: 2g`; flags `--no-sandbox --disable-gpu --disable-dev-shm-usage` (from HolyClaude).
- [0.5] 2026-10-13 — Don't put SQLite databases on SMB/CIFS mounts (locking fails); use polling watchers there.
- [0.7] 2026-10-13 — The firecrawl plugin's skills are installed but the `firecrawl` CLI is not on PATH; use WebFetch/WebSearch or Playwright.
- [0.7] 2026-10-13 — Playwright MCP is available and Chromium is preinstalled at /opt/pw-browsers; never run `playwright install`.
- [0.6] 2026-10-13 — Skill frontmatter descriptions can contain escaped quotes, literal `\n`, and YAML `>` blocks; parse all three.
- [0.9] 2026-10-13 — Cloud containers are ephemeral: anything learned must be committed and pushed, or it's lost.
