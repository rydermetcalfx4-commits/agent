# webscope

An **authorized** web-application assessment orchestrator for cloud-hosted apps.
Point it at a target you own or are contractually authorized to test; it runs
recon + enumeration + misconfiguration/vulnerability detection and writes a
prioritized findings report.

It is **read-only**. It does not exploit, log in, gain access, or modify the
target. Exploitation of confirmed findings is a deliberate, human-driven step
that lives outside this tool on purpose — that's how real engagements avoid
outages and scope blowouts.

## Why this shape

The part of a pentest that genuinely benefits from automation is the
**assessment pipeline**: discover the attack surface, flag what's wrong, rank
it. Exploitation is judgment work you do by hand (or with targeted tools like
Burp, sqlmap, Metasploit) against *specific confirmed* findings. webscope
automates the first part and hands you a report to drive the second.

## Requirements

Python 3.9+. **No third-party packages** — standard library only, so it's
plug-and-play. `nmap` and `nuclei` are used automatically *if present* (with
`--tools`), and silently skipped if not.

## Install

**One-line install** (drops `webscope` on your PATH, no sudo):

```bash
curl -fsSL https://raw.githubusercontent.com/rydermetcalfx4-commits/agent/main/projects/webscope/install.sh | bash
webscope app.example.com
```

> Until PR #1 is merged, install from the branch instead:
> `curl -fsSL https://raw.githubusercontent.com/rydermetcalfx4-commits/agent/claude/wizardly-heisenberg-4x8g7x/projects/webscope/install.sh | WEBSCOPE_REF=claude/wizardly-heisenberg-4x8g7x bash`

**Or grab the single file and run it** (nothing installed):

```bash
curl -fsSL https://raw.githubusercontent.com/rydermetcalfx4-commits/agent/main/projects/webscope/webscope.py -o webscope.py
python3 webscope.py app.example.com
```

(As always, pipe-to-shell runs code from the internet — the one file is small;
read it first if you like.)

## Usage

### Quick start — one command

```bash
python3 webscope.py app.example.com
```

That's it. The scheme defaults to `https://`, the scope auto-limits to exactly
that host, and your git/OS identity is recorded as the authorizer. It shows you
the target + scope and asks you to confirm you're authorized, then runs and
writes `webscope-report.json` / `webscope-report.md`.

### Multi-host / full control

For more than one host, subdomains, or CIDR ranges, use a scope file:

```bash
cp scope.example.yaml scope.yaml
$EDITOR scope.yaml                       # list the hosts/ranges you're authorized to test

python3 webscope.py https://app.example.com \
    --scope scope.yaml \
    --authorized-by "Jane Client <jane@example.com>" \
    --engagement "SOW-2026-014" \
    --out report \
    --tools                              # optional: also run nmap/nuclei if installed
```

### CI / unattended

```bash
python3 webscope.py app.example.com --yes --authorized-by "ci@example.com"
```

`--yes` skips the interactive confirmation but *requires* an explicit
`--authorized-by`, so unattended use stays deliberate.

Outputs `report.json` (machine-readable) and `report.md` (human-readable).

### Flags

| Flag | Meaning |
| --- | --- |
| `target` | Base URL or bare host (positional); scheme defaults to `https://` |
| `--scope` | Path to the allowlist file. Omit to auto-scope to the target host only |
| `--authorized-by` | Who authorized the engagement (defaults to your git/OS identity) |
| `--engagement` | SOW / ticket reference (recorded in the report) |
| `--out` | Output path prefix (default `webscope-report`) |
| `--rate` | Max requests/second (default 5) |
| `--timeout` | Per-request timeout seconds (default 15) |
| `--tools` | Also orchestrate `nmap`/`nuclei` if on PATH |
| `--yes` | Skip the interactive authorization confirmation (for CI) |

## What it checks

- Reachability and server fingerprint
- TLS: HTTPS enforcement, protocol version, certificate expiry
- Security headers: HSTS (and quality), CSP, X-Content-Type-Options,
  X-Frame-Options, Referrer-Policy, Permissions-Policy
- Cookie flags: Secure / HttpOnly / SameSite
- Version/information disclosure headers
- Read-only probe of commonly-misconfigured paths (`.git/config`, `.env`,
  `/actuator/env`, Swagger/OpenAPI, backups, admin surfaces, …) — status only
- Optional `nuclei` template scan and `nmap` service scan (with `--tools`)

## Safety model

1. **Scope allowlist is mandatory and enforced per request.** Every outbound
   request checks the host against the allowlist; an out-of-scope URL raises
   and aborts. An empty allowlist refuses to run.
2. **Read-only.** Only `GET`; response bodies are capped; nothing is written to
   the target.
3. **Rate-limited** so you don't DoS your own client.
4. **Auditable.** Authorizer, engagement ref, timestamps, and every request URL
   are recorded in the report.

## Legal

Unauthorized access to computer systems is illegal (CFAA, Computer Misuse Act,
and equivalents). Run this only against systems you own or have explicit written
authorization to test. You are responsible for staying within scope.
