# Running the agent in HolyClaude

[HolyClaude](https://github.com/CoderLuii/HolyClaude) is a Docker image with Claude Code, a web UI, headless Chromium, other AI CLIs, and 50+ dev tools.

```bash
cd holyclaude
docker compose up -d
# open http://localhost:3001 and sign in
```

This repo is mounted at `/workspace/agent`, so `CLAUDE.md`, the skills, and the hooks load as usual.
`scripts/scrape_self.sh` will report `HolyClaude container: yes` and a much shorter "Missing" list.

- `environment-full.md` / `environment-slim.md`: HolyClaude's own notes on what's installed (upstream copies, refreshed by `scripts/import_sources.sh`).
- Notifications: set a `NOTIFY_*` variable in `docker-compose.yaml` and `touch data/claude/notify-on`.
- `data/` holds credentials; it's git-ignored. Don't commit it.
