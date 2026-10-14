#!/usr/bin/env python3
"""Scrape upstream sources (sources.json) and integrate them into this repo.

  python3 scripts/import_sources.py              # use revisions pinned in sources.lock
  python3 scripts/import_sources.py --update     # pull latest upstream, re-pin
  python3 scripts/import_sources.py --only ecc   # one source (comma-separated ids)
  SRC_DIR=/path/to/clones python3 ...            # reuse a clone cache

Outputs: catalog/<id>/<kind>s/<name>.md (text only), catalog/INDEX.tsv,
promoted skill dirs in .claude/skills (tracked in .claude/skills/.vendored),
catalog/external/*.md link indexes, THIRD_PARTY.md, sources.lock.
"""
import argparse, csv, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "sources.json").read_text())["sources"]
LOCK = ROOT / "sources.lock"
SKILLS = ROOT / ".claude" / "skills"
VENDORED = SKILLS / ".vendored"
CATALOG = ROOT / "catalog"
SKIP_PARTS = {".git", "node_modules", "tests", "test", "__pycache__"}


def git(*args, cwd=None):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def fetch(src, rev, src_dir, update):
    dest = src_dir / src["id"]
    url = f"https://github.com/{src['repo']}"
    if not (dest / ".git").exists():
        git("clone", "-q", "--depth", "1", url, str(dest))
    if rev and not update and git("rev-parse", "HEAD", cwd=dest) != rev:
        git("fetch", "-q", "--depth", "1", "origin", rev, cwd=dest)
        git("checkout", "-q", rev, cwd=dest)
    elif update:
        git("fetch", "-q", "--depth", "1", "origin", "HEAD", cwd=dest)
        git("checkout", "-q", "FETCH_HEAD", cwd=dest)
    return dest, git("rev-parse", "HEAD", cwd=dest)


def frontmatter(text):
    """Minimal YAML frontmatter reader: top-level scalars, quoted values, and >/| blocks."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    out, key, block = {}, None, []
    for line in m.group(1).splitlines():
        if key and (line.startswith((" ", "\t")) or not line.strip()):
            block.append(line.strip())
            continue
        if key:
            out[key], key, block = " ".join(b for b in block if b), None, []
        kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not kv:
            continue
        k, v = kv.groups()
        if v in (">", "|", ">-", "|-", ">+", "|+"):
            key = k
        else:
            out[k] = v.strip().strip('"').strip("'").replace('\\"', '"')
    if key:
        out[key] = " ".join(b for b in block if b)
    return out


def one_line(s, n=200):
    s = re.sub(r"\s+", " ", (s or "").replace("\\n", " ")).strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def wanted(rel, rule):
    if SKIP_PARTS & set(Path(rel).parts):
        return False
    return not any(x in rel for x in rule.get("exclude", []))


def entry_name(path, kind, rule):
    name = path.parent.name if kind == "skill" else path.stem
    for suf in rule.get("name_strip", []):
        name = name[: -len(suf)] if name.endswith(suf) else name
    return name.lstrip("-") or name


def build_catalog(src, repo_dir, rev):
    out_root = CATALOG / src["id"]
    shutil.rmtree(out_root, ignore_errors=True)  # catalog/<id>/ is fully owned by this source
    rows, seen = [], set()
    for rule in src.get("catalog", []):
        kind = rule["kind"]
        for p in sorted(repo_dir.glob(rule["glob"])):
            rel = p.relative_to(repo_dir).as_posix()
            if not p.is_file() or not wanted(rel, rule):
                continue
            name = entry_name(p, kind, rule)
            if (kind, name) in seen:  # disambiguate with the nearest distinguishing folder
                anchor = p.parent.parent if kind == "skill" else p.parent
                name = f"{anchor.name}--{name}"
            if (kind, name) in seen:
                continue
            seen.add((kind, name))
            text = p.read_text(errors="replace")
            fm = frontmatter(text)
            desc = fm.get("description") or next((l for l in text.splitlines() if l.strip() and not l.startswith(("#", "---"))), "")
            dest = out_root / f"{kind}s" / f"{name}.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text)
            rows.append([kind, src["id"], name, one_line(desc),
                         dest.relative_to(ROOT).as_posix(),
                         f"https://github.com/{src['repo']}/blob/{rev[:12]}/{rel}"])
    return rows


def promote(src, repo_dir, vendored):
    for rel in src.get("promote", []):
        s = repo_dir / rel
        if not s.is_dir():
            print(f"  ! promote missing: {src['id']}:{rel}", file=sys.stderr)
            continue
        dest = SKILLS / s.name
        shutil.rmtree(dest, ignore_errors=True)
        shutil.copytree(s, dest, ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__"))
        for f in dest.rglob("*.md"):
            t = f.read_text(errors="replace")
            for a, b in src.get("rewrite", {}).items():
                t = t.replace(a, b)
            f.write_text(t)
        vendored[s.name] = src["id"]


def copy_files(src, repo_dir):
    for a, b in src.get("files", {}).items():
        dest = ROOT / b
        dest.parent.mkdir(parents=True, exist_ok=True)
        t = (repo_dir / a).read_text(errors="replace")
        for x, y in src.get("file_rewrite", {}).get(a, {}).items():
            t = t.replace(x, y)
        dest.write_text(t)


def external_index(src, repo_dir):
    ix = src.get("external_index")
    if not ix:
        return
    out = ROOT / ix["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# External index: {src['repo']}", "",
             f"Links only (license: {src['license']}). Not vendored; install one when a task needs it, then `/evolve`.", ""]
    if ix["type"] == "readme":
        on = False
        for l in (repo_dir / ix["path"]).read_text().splitlines():
            if l.startswith(ix["start"]):
                on = True
            elif l.startswith(ix["end"]):
                on = False
            elif on and l.startswith("### "):
                lines += ["", "## " + l[4:]]
            elif on and l.startswith("- [") and "](./" not in l:
                lines.append(l)
    else:  # csv: names, links and categories only
        rows = [r for r in csv.DictReader(open(repo_dir / ix["path"], newline="")) if r.get("Active", "TRUE").upper() == "TRUE"]
        for cat in sorted({r["Category"] for r in rows}):
            lines += ["", f"## {cat}"]
            for r in sorted((r for r in rows if r["Category"] == cat), key=lambda r: r["Display Name"].lower()):
                sub = f" — {r['Sub-Category']}" if r.get("Sub-Category") else ""
                lines.append(f"- [{r['Display Name']}]({r['Link']}){sub}")
    out.write_text("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--update", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    only = set(filter(None, a.only.split(",")))
    lock = json.loads(LOCK.read_text()) if LOCK.exists() else {}
    src_dir = Path(os.environ.get("SRC_DIR") or tempfile.mkdtemp(prefix="agent-sources-"))
    vendored = dict(l.split("\t") for l in VENDORED.read_text().splitlines() if "\t" in l) if VENDORED.exists() else {}

    index_path = CATALOG / "INDEX.tsv"
    rows = [r.split("\t") for r in index_path.read_text().splitlines()[1:]] if index_path.exists() else []
    for src in CFG:
        if only and src["id"] not in only:
            continue
        if not any(src.get(k) for k in ("catalog", "promote", "files", "external_index")):
            continue  # ideas-only source: listed in THIRD_PARTY.md, nothing fetched
        repo_dir, rev = fetch(src, lock.get(src["id"]), src_dir, a.update)
        lock[src["id"]] = rev
        rows = [r for r in rows if r[1] != src["id"]]
        rows += build_catalog(src, repo_dir, rev)
        # drop skills this source promoted before but no longer lists
        for name, sid in list(vendored.items()):
            if sid == src["id"]:
                shutil.rmtree(SKILLS / name, ignore_errors=True)
                del vendored[name]
        promote(src, repo_dir, vendored)
        copy_files(src, repo_dir)
        external_index(src, repo_dir)
        print(f"{src['id']:<20} {rev[:12]}  catalog={sum(r[1] == src['id'] for r in rows)}  promoted={sum(v == src['id'] for v in vendored.values())}")

    rows.sort(key=lambda r: (r[1], r[0], r[2]))
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("kind\tsource\tname\tdescription\tpath\tupstream\n" + "".join("\t".join(r) + "\n" for r in rows))
    VENDORED.write_text("".join(f"{k}\t{v}\n" for k, v in sorted(vendored.items())))
    LOCK.write_text(json.dumps(dict(sorted(lock.items())), indent=2) + "\n")

    t = ["# Third-party sources", "", "Generated by `scripts/import_sources.py` from `sources.json`; revisions pinned in `sources.lock`.", "",
         "| Source | Commit | License | Catalog | Promoted to .claude/skills |", "|---|---|---|---|---|"]
    for src in CFG:
        n = sum(r[1] == src["id"] for r in rows)
        p = " ".join(f"`{k}`" for k, v in sorted(vendored.items()) if v == src["id"]) or "—"
        rev = lock.get(src["id"], "")[:12] or "ideas only"
        t.append(f"| [{src['repo']}](https://github.com/{src['repo']}) | `{rev}` | {src['license']} | {n} | {p} |")
    (ROOT / "THIRD_PARTY.md").write_text("\n".join(t) + "\n")
    print(f"index: {len(rows)} entries; promoted: {len(vendored)} skills")


if __name__ == "__main__":
    main()
