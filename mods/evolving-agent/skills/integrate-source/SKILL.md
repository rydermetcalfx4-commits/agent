---
name: integrate-source
description: "Scrape a GitHub repo, list, or search topic and fold its useful ideas into this project safely."
---

# Integrate a source

For "use everything from <repo / awesome-list / GitHub search>". Done right, the result is a few high-value changes,
not a dump of 1,000 skills.

1. **Find repos.** A GitHub search URL may be blocked (cloud sessions allow only repo-scoped GitHub access); then use
   web search for the most-starred repos on the topic, and say so.
2. **Clone into a scratch dir**, never the project: `git clone -q --depth 1 https://github.com/<owner>/<repo> <scratch>/<id>`.
3. **Survey**: license (none → ideas only), counts of SKILL.md / agents / commands / hook scripts, last commit, architecture.
4. **Read for mechanisms, not volume**: hooks, memory, learning loops, authoring standards. What makes it better than what
   this project has? Write findings with an adopted/not-adopted table.
5. **Adopt ideas as the project's own code**, credited by repo name.
6. **Vendoring third-party files** (skills with scripts especially): list every script, grep for network calls,
   `eval`/`exec`, credential paths and installs, then get the user's **explicit** approval of that specific import.
7. **Record**: lessons in `.evolving-agent/learnings.md`, then run the evolve skill.

Gotchas: many hosts are egress-blocked (403 / ENOTFOUND), so switch sources rather than retry. Copied cross-references
like `<plugin>:<skill>` break and need rewriting. For CC BY-NC-ND lists, index names and links only.
