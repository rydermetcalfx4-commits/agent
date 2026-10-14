#!/usr/bin/env python3
"""
webscope — an authorized web-app assessment orchestrator.

Scope-gated recon + enumeration + misconfiguration/vulnerability detection for
targets you OWN or are CONTRACTUALLY AUTHORIZED to test. It produces a
prioritized findings report; it does NOT exploit, gain access, or modify the
target. Exploitation of confirmed findings is a deliberate, human-driven step
that lives outside this tool on purpose.

Design goals:
  * Plug and play: standard library only. `python3 webscope.py --help`.
  * Safe by construction: refuses to touch anything not in the scope allowlist;
    read-only requests; rate-limited; honours a global timeout.
  * Auditable: records who authorized the engagement and when, and logs every
    request made.

Usage:
  python3 webscope.py \
      --target https://app.example.com \
      --scope scope.yaml \
      --authorized-by "Jane Client <jane@example.com>" \
      --engagement "SOW-2026-014" \
      --out report

Only run this against systems you are authorized to test. Unauthorized access
to computer systems is illegal.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import ipaddress
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

USER_AGENT = "webscope/1.0 (authorized-assessment)"


def _utcnow() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)

# Read-only paths that commonly leak config or expose admin surfaces when
# misconfigured. We only GET them and record the status code — this is a
# misconfiguration check, not exploitation.
SENSITIVE_PATHS = [
    "/.git/config",
    "/.env",
    "/.env.local",
    "/.svn/entries",
    "/.DS_Store",
    "/robots.txt",
    "/sitemap.xml",
    "/.well-known/security.txt",
    "/admin",
    "/admin/login",
    "/wp-admin/",
    "/wp-login.php",
    "/phpinfo.php",
    "/server-status",
    "/actuator",
    "/actuator/health",
    "/actuator/env",
    "/api",
    "/api/v1",
    "/swagger-ui.html",
    "/swagger.json",
    "/openapi.json",
    "/.well-known/openid-configuration",
    "/backup.zip",
    "/backup.sql",
    "/config.json",
]

SECURITY_HEADERS = {
    "strict-transport-security": ("HSTS not set", "medium"),
    "content-security-policy": ("Content-Security-Policy not set", "medium"),
    "x-content-type-options": ("X-Content-Type-Options not set (MIME sniffing)", "low"),
    "x-frame-options": ("X-Frame-Options not set (clickjacking)", "low"),
    "referrer-policy": ("Referrer-Policy not set", "low"),
    "permissions-policy": ("Permissions-Policy not set", "info"),
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


# --------------------------------------------------------------------------- #
# Findings & report
# --------------------------------------------------------------------------- #
@dataclass
class Finding:
    title: str
    severity: str  # critical|high|medium|low|info
    detail: str
    evidence: str = ""
    recommendation: str = ""


@dataclass
class Report:
    target: str
    authorized_by: str
    engagement: str
    started_at: str
    finished_at: str = ""
    scope: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    requests_made: list[str] = field(default_factory=list)
    tool_runs: dict[str, str] = field(default_factory=dict)

    def add(self, f: Finding) -> None:
        self.findings.append(f)

    def sorted_findings(self) -> list[Finding]:
        return sorted(self.findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 9))


# --------------------------------------------------------------------------- #
# Scope enforcement — the safety core
# --------------------------------------------------------------------------- #
class Scope:
    """Allowlist of hosts/CIDRs this run is permitted to touch.

    Supports, one per line (a minimal YAML-ish / plain list format):
      example.com            exact host
      *.example.com          host and any subdomain
      10.0.0.0/24            CIDR range (matched against resolved IPs)
    Lines starting with '#' and a leading 'scope:' / '-' are ignored/stripped,
    so a plain YAML list works without a YAML dependency.
    """

    def __init__(self, patterns: list[str]):
        self.exact: set[str] = set()
        self.wildcards: list[str] = []
        self.cidrs: list[ipaddress._BaseNetwork] = []
        for raw in patterns:
            p = raw.strip().lstrip("-").strip().strip("'\"")
            if not p or p.startswith("#") or p.lower() == "scope:":
                continue
            try:
                self.cidrs.append(ipaddress.ip_network(p, strict=False))
                continue
            except ValueError:
                pass
            if p.startswith("*."):
                self.wildcards.append(p[2:].lower())
            else:
                self.exact.add(p.lower())

    @classmethod
    def from_file(cls, path: str) -> "Scope":
        with open(path, "r", encoding="utf-8") as fh:
            return cls(fh.read().splitlines())

    def allows_host(self, host: str) -> bool:
        host = host.lower().rstrip(".")
        if host in self.exact:
            return True
        for w in self.wildcards:
            if host == w or host.endswith("." + w):
                return True
        if self.cidrs:
            for ip in _resolve_all(host):
                addr = ipaddress.ip_address(ip)
                if any(addr in net for net in self.cidrs):
                    return True
        return False

    def as_list(self) -> list[str]:
        return (
            sorted(self.exact)
            + [f"*.{w}" for w in self.wildcards]
            + [str(c) for c in self.cidrs]
        )

    def is_empty(self) -> bool:
        return not (self.exact or self.wildcards or self.cidrs)


def _resolve_all(host: str) -> list[str]:
    try:
        return list({ai[4][0] for ai in socket.getaddrinfo(host, None)})
    except socket.gaierror:
        return []


class ScopeError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# Rate-limited, scope-checked HTTP client
# --------------------------------------------------------------------------- #
class Client:
    def __init__(self, scope: Scope, report: Report, rate: float, timeout: float):
        self.scope = scope
        self.report = report
        self.min_interval = 1.0 / rate if rate > 0 else 0.0
        self.timeout = timeout
        self._last = 0.0

    def _throttle(self) -> None:
        if self.min_interval:
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
        self._last = time.monotonic()

    def get(self, url: str) -> Optional[tuple[int, dict[str, str], bytes]]:
        host = urlparse(url).hostname or ""
        if not self.scope.allows_host(host):
            raise ScopeError(f"Refusing out-of-scope request to {host!r}: {url}")
        self._throttle()
        self.report.requests_made.append(url)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT}, method="GET")
        ctx = ssl.create_default_context()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                body = resp.read(65536)  # cap: we only need headers + a sample
                headers = {k.lower(): v for k, v in resp.headers.items()}
                return resp.status, headers, body
        except urllib.error.HTTPError as e:
            headers = {k.lower(): v for k, v in (e.headers or {}).items()}
            return e.code, headers, b""
        except (urllib.error.URLError, ssl.SSLError, socket.timeout, ConnectionError, OSError):
            return None


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #
def check_reachability(client: Client, report: Report, base: str) -> Optional[dict[str, str]]:
    res = client.get(base)
    if res is None:
        report.add(Finding(
            "Target unreachable", "info",
            f"Could not complete an HTTPS request to {base}.",
            recommendation="Confirm the host, port, and that you can reach it from this network.",
        ))
        return None
    status, headers, _ = res
    report.add(Finding(
        "Base URL reachable", "info",
        f"{base} responded with HTTP {status}.",
        evidence=f"Server: {headers.get('server', 'n/a')}",
    ))
    return headers


def check_security_headers(report: Report, headers: dict[str, str]) -> None:
    for name, (msg, sev) in SECURITY_HEADERS.items():
        if name not in headers:
            report.add(Finding(
                msg, sev,
                f"Response is missing the `{name}` header.",
                recommendation=f"Set an appropriate `{name}` header on all responses.",
            ))
    # HSTS quality
    hsts = headers.get("strict-transport-security", "")
    if hsts:
        m = re.search(r"max-age=(\d+)", hsts)
        if m and int(m.group(1)) < 15552000:
            report.add(Finding(
                "HSTS max-age below 180 days", "low",
                f"HSTS max-age is {m.group(1)}s.",
                recommendation="Use max-age >= 15552000 and consider includeSubDomains; preload.",
            ))


def check_cookies(report: Report, headers: dict[str, str]) -> None:
    # urllib collapses multiple Set-Cookie into one; still catches the common case.
    raw = headers.get("set-cookie", "")
    if not raw:
        return
    low = raw.lower()
    issues = []
    if "secure" not in low:
        issues.append("missing Secure")
    if "httponly" not in low:
        issues.append("missing HttpOnly")
    if "samesite" not in low:
        issues.append("missing SameSite")
    if issues:
        report.add(Finding(
            "Cookie flags weak", "medium",
            "Set-Cookie: " + ", ".join(issues) + ".",
            evidence=raw[:200],
            recommendation="Set Secure, HttpOnly, and SameSite on session cookies.",
        ))


def check_info_disclosure(report: Report, headers: dict[str, str]) -> None:
    for h in ("server", "x-powered-by", "x-aspnet-version", "x-generator"):
        if h in headers and any(ch.isdigit() for ch in headers[h]):
            report.add(Finding(
                f"Version disclosure via `{h}`", "low",
                f"{h}: {headers[h]}",
                recommendation=f"Suppress or genericise the `{h}` header to avoid fingerprinting.",
            ))


def check_tls(report: Report, base: str, timeout: float) -> None:
    parsed = urlparse(base)
    if parsed.scheme != "https":
        report.add(Finding(
            "Not using HTTPS", "high",
            f"Target base URL uses {parsed.scheme}.",
            recommendation="Serve the application exclusively over HTTPS and redirect HTTP.",
        ))
        return
    host = parsed.hostname or ""
    port = parsed.port or 443
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                proto = ssock.version()
    except Exception as e:  # noqa: BLE001 - report any TLS failure
        report.add(Finding(
            "TLS handshake failed", "medium",
            f"Could not validate the certificate for {host}:{port}: {e}",
            recommendation="Investigate certificate validity and chain.",
        ))
        return
    if proto in ("TLSv1", "TLSv1.1", "SSLv3"):
        report.add(Finding(
            "Weak TLS protocol negotiated", "medium",
            f"Server negotiated {proto}.",
            recommendation="Disable TLS < 1.2.",
        ))
    not_after = cert.get("notAfter")
    if not_after:
        try:
            exp = _dt.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
            days = (exp.replace(tzinfo=_dt.timezone.utc) - _utcnow()).days
            sev = "high" if days < 0 else "medium" if days < 14 else "info"
            report.add(Finding(
                "TLS certificate expiry", sev,
                f"Certificate expires in {days} days ({not_after}).",
                recommendation="Renew before expiry; automate renewal.",
            ))
        except ValueError:
            pass


def check_sensitive_paths(client: Client, report: Report, base: str) -> None:
    for path in SENSITIVE_PATHS:
        url = urljoin(base, path)
        res = client.get(url)
        if res is None:
            continue
        status, _, body = res
        if status == 200 and body:
            sev = "info"
            if path in ("/.git/config", "/.env", "/.env.local", "/backup.sql",
                        "/backup.zip", "/actuator/env", "/config.json"):
                sev = "high"
            elif path in ("/phpinfo.php", "/server-status", "/.svn/entries",
                          "/swagger.json", "/openapi.json", "/actuator"):
                sev = "medium"
            report.add(Finding(
                f"Accessible path: {path}", sev,
                f"GET {url} returned 200 with a non-empty body.",
                evidence=body[:120].decode("utf-8", "replace").replace("\n", " "),
                recommendation="Confirm this path should be public; restrict if it leaks data or admin surface.",
            ))


# --------------------------------------------------------------------------- #
# Optional external-tool orchestration (degrades gracefully)
# --------------------------------------------------------------------------- #
def run_optional_tools(report: Report, base: str, scope: Scope, enable: bool) -> None:
    if not enable:
        return
    host = urlparse(base).hostname or ""
    # nuclei: community vuln templates, scoped to the single target.
    if shutil.which("nuclei"):
        try:
            out = subprocess.run(
                ["nuclei", "-u", base, "-silent", "-nc", "-timeout", "10"],
                capture_output=True, text=True, timeout=600, check=False,
            )
            report.tool_runs["nuclei"] = (out.stdout or out.stderr)[:4000]
            for line in out.stdout.splitlines():
                if line.strip():
                    report.add(Finding(
                        "nuclei finding", "medium", line.strip(),
                        recommendation="Review the nuclei template that fired and validate.",
                    ))
        except (subprocess.TimeoutExpired, OSError) as e:
            report.tool_runs["nuclei"] = f"error: {e}"
    # nmap: top-port service scan, only if the host itself is in scope.
    if shutil.which("nmap") and scope.allows_host(host):
        try:
            out = subprocess.run(
                ["nmap", "-Pn", "-T3", "--top-ports", "100", "-sV", host],
                capture_output=True, text=True, timeout=600, check=False,
            )
            report.tool_runs["nmap"] = (out.stdout or out.stderr)[:4000]
        except (subprocess.TimeoutExpired, OSError) as e:
            report.tool_runs["nmap"] = f"error: {e}"


# --------------------------------------------------------------------------- #
# Report writers
# --------------------------------------------------------------------------- #
def write_reports(report: Report, out_prefix: str) -> tuple[str, str]:
    report.finished_at = _utcnow().isoformat()
    json_path = out_prefix + ".json"
    md_path = out_prefix + ".md"
    data = asdict(report)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    counts: dict[str, int] = {}
    for f in report.findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    lines = [
        f"# webscope report — {report.target}",
        "",
        f"- **Engagement:** {report.engagement}",
        f"- **Authorized by:** {report.authorized_by}",
        f"- **Scope:** {', '.join(report.scope)}",
        f"- **Started:** {report.started_at}",
        f"- **Finished:** {report.finished_at}",
        f"- **Requests made:** {len(report.requests_made)}",
        "",
        "## Summary",
        "",
        "| Severity | Count |",
        "| --- | --- |",
    ]
    for sev in ("critical", "high", "medium", "low", "info"):
        if counts.get(sev):
            lines.append(f"| {sev} | {counts[sev]} |")
    lines += ["", "## Findings", ""]
    for f in report.sorted_findings():
        lines.append(f"### [{f.severity.upper()}] {f.title}")
        lines.append("")
        lines.append(f.detail)
        if f.evidence:
            lines.append("")
            lines.append(f"> Evidence: `{f.evidence}`")
        if f.recommendation:
            lines.append("")
            lines.append(f"**Recommendation:** {f.recommendation}")
        lines.append("")
    if report.tool_runs:
        lines += ["## External tool output", ""]
        for name, out in report.tool_runs.items():
            lines += [f"### {name}", "", "```", out.strip(), "```", ""]
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return json_path, md_path


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _default_authorizer() -> str:
    """Best-effort identity for the --authorized-by record (git, then OS user)."""
    try:
        name = subprocess.run(
            ["git", "config", "user.name"], capture_output=True, text=True, timeout=3, check=False
        ).stdout.strip()
        email = subprocess.run(
            ["git", "config", "user.email"], capture_output=True, text=True, timeout=3, check=False
        ).stdout.strip()
        if name and email:
            return f"{name} <{email}>"
        if name:
            return name
    except OSError:
        pass
    return os.environ.get("USER") or os.environ.get("USERNAME") or "unspecified"


def _normalize_target(raw: str) -> str:
    """Accept bare hosts; default to https:// so `webscope.py app.example.com` works."""
    if "://" not in raw:
        return "https://" + raw
    return raw


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="webscope.py",
        description="Authorized web-app assessment orchestrator (read-only).",
        epilog=(
            "Quick start:  python3 webscope.py https://app.example.com\n"
            "Only run against systems you own or are authorized to test."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("target", nargs="?", help="Base URL or host, e.g. https://app.example.com")
    p.add_argument("--target", dest="target_flag", help=argparse.SUPPRESS)
    p.add_argument("--scope", help="Scope allowlist file. Omit to auto-scope to the target host only.")
    p.add_argument("--authorized-by", help="Who authorized this engagement (defaults to your git/OS identity)")
    p.add_argument("--engagement", default="(unspecified)", help="Engagement / SOW reference")
    p.add_argument("--out", default="webscope-report", help="Output path prefix")
    p.add_argument("--rate", type=float, default=5.0, help="Max requests/second (default 5)")
    p.add_argument("--timeout", type=float, default=15.0, help="Per-request timeout seconds")
    p.add_argument("--tools", action="store_true", help="Also run nmap/nuclei if installed")
    p.add_argument("--yes", action="store_true", help="Skip the interactive authorization confirmation (CI)")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    raw_target = args.target or args.target_flag
    if not raw_target:
        print("error: give a target, e.g.  python3 webscope.py https://app.example.com", file=sys.stderr)
        return 2
    target = _normalize_target(raw_target)
    host = urlparse(target).hostname
    if not host:
        print(f"error: could not parse a host from {raw_target!r}", file=sys.stderr)
        return 2

    # Scope: explicit file, or auto-scope to just the target host.
    auto_scoped = False
    if args.scope:
        if not os.path.exists(args.scope):
            print(f"error: scope file not found: {args.scope}", file=sys.stderr)
            return 2
        scope = Scope.from_file(args.scope)
        if scope.is_empty():
            print("error: scope allowlist is empty — refusing to run.", file=sys.stderr)
            return 2
        if not scope.allows_host(host):
            print(f"error: target host {host!r} is NOT in the scope allowlist — refusing to run.", file=sys.stderr)
            print(f"       scope: {', '.join(scope.as_list())}", file=sys.stderr)
            return 2
    else:
        scope = Scope([host])
        auto_scoped = True

    authorized_by = args.authorized_by or _default_authorizer()

    # The confirmation prompt is the authorization gate. In non-interactive
    # (--yes) runs, require an explicit --authorized-by so CI use is deliberate.
    if args.yes:
        if not args.authorized_by:
            print("error: --yes requires an explicit --authorized-by.", file=sys.stderr)
            return 2
    else:
        print("You are about to run an authorized assessment against:")
        print(f"  target     : {target}")
        print(f"  scope      : {', '.join(scope.as_list())}" + ("  (auto-scoped to target host)" if auto_scoped else ""))
        print(f"  authorized : {authorized_by}")
        print(f"  engagement : {args.engagement}")
        try:
            ans = input("Confirm you own or are authorized to test this target [yes/NO]: ").strip().lower()
        except EOFError:
            ans = ""
        if ans not in ("y", "yes"):
            print("Aborted.")
            return 1

    report = Report(
        target=target,
        authorized_by=authorized_by,
        engagement=args.engagement,
        started_at=_utcnow().isoformat(),
        scope=scope.as_list(),
    )
    client = Client(scope, report, rate=args.rate, timeout=args.timeout)

    print(f"[*] Assessing {target} ...")
    try:
        headers = check_reachability(client, report, target)
        check_tls(report, target, args.timeout)
        if headers is not None:
            check_security_headers(report, headers)
            check_cookies(report, headers)
            check_info_disclosure(report, headers)
            check_sensitive_paths(client, report, target)
        run_optional_tools(report, target, scope, args.tools)
    except ScopeError as e:
        print(f"[!] {e}", file=sys.stderr)
        return 3

    json_path, md_path = write_reports(report, args.out)
    n = len(report.findings)
    print(f"[+] Done. {n} finding(s) across {len(report.requests_made)} request(s).")
    print(f"    JSON: {json_path}")
    print(f"    MD  : {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
