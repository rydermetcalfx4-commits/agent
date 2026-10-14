# Learnings

Format: `- [confidence] YYYY-MM-DD — lesson`. 0.3 tentative … 1.0 certain. New 0.5 (0.7 if the user said it);
re-observed +0.1; contradicted −0.2; below 0.3 drop. Lessons at ≥ 0.7 are injected into every session by the
evolving-agent plugin. Keep under 60 lines; merge or drop stale ones.

Seeded with portable lessons from the agent this plugin was cloned from:

- [0.7] 2026-10-14 — Guards and log parsers must split commands per segment and skip heredocs and quoted messages; grepping the whole command string gives false positives.
- [0.7] 2026-10-14 — Bulk skill sets belong in a searchable catalog, not the skills folder: every skill description is loaded into every session.
- [0.7] 2026-10-14 — Third-party repos: clone into a scratch dir, read scripts before vendoring, check the license (none = ideas only), pin the commit.
- [0.6] 2026-10-14 — Skill descriptions route on their first ~60 characters; lead with when-to-use.
- [0.6] 2026-10-14 — In cloud sessions GitHub search is blocked; find repos with web search, then `git clone --depth 1`.
- [0.6] 2026-10-13 — Ephemeral containers lose everything not committed and pushed; commit memory changes.
