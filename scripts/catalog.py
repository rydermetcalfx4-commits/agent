#!/usr/bin/env python3
"""Search the on-demand catalog built by scripts/import_sources.py.

  python3 scripts/catalog.py search debugging root cause   # ranked matches
  python3 scripts/catalog.py search -k agent kubernetes    # only agents (skill|agent|command)
  python3 scripts/catalog.py show ecc/skills/verification-loop
  python3 scripts/catalog.py promote superpowers skills/brainstorming   # add to sources.json, then re-import
  python3 scripts/catalog.py stats
"""
import json, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "catalog" / "INDEX.tsv"


def rows():
    if not INDEX.exists():
        sys.exit("catalog/INDEX.tsv missing: run python3 scripts/import_sources.py first")
    lines = INDEX.read_text().splitlines()
    head = lines[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in lines[1:]]


def search(args):
    kind = None
    if args[:1] == ["-k"]:
        kind, args = args[1], args[2:]
    terms = [t.lower() for t in args]
    scored = []
    for r in rows():
        if kind and r["kind"] != kind:
            continue
        name, desc = r["name"].lower(), r["description"].lower()
        if not all(t in name or t in desc for t in terms):
            continue
        scored.append((sum(3 * (t in name) + desc.count(t) for t in terms), r))
    for score, r in sorted(scored, key=lambda x: -x[0])[:25]:
        print(f"{r['source']}/{r['kind']}s/{r['name']}\t{r['description'][:120]}")
    print(f"({len(scored)} matches)", file=sys.stderr)


def show(ref):
    path = ROOT / "catalog" / f"{ref}.md"
    print(path.read_text() if path.exists() else f"not found: {path}")


def promote(source, rel):
    cfg_path = ROOT / "sources.json"
    cfg = json.loads(cfg_path.read_text())
    src = next((s for s in cfg["sources"] if s["id"] == source), None)
    if not src:
        sys.exit(f"unknown source {source}")
    if rel not in src.setdefault("promote", []):
        src["promote"].append(rel)
        cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
    print(f"added {source}:{rel} to sources.json. Review the upstream directory (it may contain scripts), then run:\n"
          f"  python3 scripts/import_sources.py --only {source}")


def stats():
    c = Counter((r["source"], r["kind"]) for r in rows())
    for (s, k), n in sorted(c.items()):
        print(f"{s:<20} {k:<8} {n}")
    print(f"total {sum(c.values())}")


if __name__ == "__main__":
    cmd, *rest = sys.argv[1:] or ["help"]
    {"search": lambda: search(rest), "show": lambda: show(rest[0]),
     "promote": lambda: promote(*rest[:2]), "stats": stats}.get(cmd, lambda: print(__doc__))()
