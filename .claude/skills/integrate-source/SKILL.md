---
name: integrate-source
description: "Scrape a GitHub repo, list, or search topic and fold the useful parts into this agent safely."
---

# Integrate a source

The workflow behind generations 2 and 3: the user points at a repo, an awesome-list, or a GitHub search, and wants me to "use
everything" from it. Done right, the result is a few high-value changes plus a searchable catalog, not a dump of 1,000 skills.

## Procedure
1. **Find the repos.** A repo URL → use it. A GitHub *search* URL → it's blocked in cloud sessions (proxy allows only
   repo-scoped GitHub endpoints). Use `WebSearch` (mode `extended`) for the most-starred repos on the topic instead, and say so.
2. **Clone into the scratchpad**, never the repo: `git clone -q --depth 1 https://github.com/<owner>/<repo> <scratchpad>/src/<id>`.
   Clone several in parallel with `&` + `wait`.
3. **Survey each repo**: license (`head LICENSE*`; none → ideas only, copy nothing), counts of `SKILL.md` / `agents/*.md` /
   `commands/*.md` / hook scripts, last commit date, and the README's own description of its architecture.
4. **Read for ideas, not volume.** For each repo ask: what mechanism makes it better than what I have? Look at hooks, memory,
   learning loops, and authoring standards. Write findings to `research/<topic>-<yyyy-mm>.md` with an adopted/not-adopted table.
5. **Adopt ideas as our own code** (skills in `.claude/skills/`, hooks in `scripts/`, rules in `CLAUDE.md`), credited by repo name.
   Test hooks with `bash scripts/test_hooks.sh`.
6. **Register bulk content** in `sources.json`: a `catalog` glob for text-only, searchable copies; `promote` only for a few
   skills worth loading every session; `files` for single files. Exclude proprietary or unlicensed parts.
7. **Review before vendoring.** List every script in each `promote` dir, and grep it for network calls, `eval`/`exec`, credential paths,
   and installs. Then get the user's **explicit** approval (a vague "do whatever" is not enough, and the auto-mode classifier blocks it)
   before running `python3 scripts/import_sources.py`.
8. **Verify and record**: `python3 scripts/doctor.py`, `python3 scripts/catalog.py stats`, lessons in `memory/learnings.md`,
   and a generation in `EVOLUTION.md` (via `/evolve`).

## Gotchas
- Many third-party hosts are egress-blocked (403 / ENOTFOUND); switch sources instead of retrying.
- Skill descriptions load every session. Promoting 20 skills costs ~4k chars of context forever, so promote sparingly.
- Upstream cross-references written as `<plugin>:<skill>` break when copied; strip the prefix with `rewrite` in `sources.json`.
- CC BY-NC-ND lists: index names and links only, never descriptions.
