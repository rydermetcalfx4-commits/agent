#!/usr/bin/env python3
"""Health check and fitness report for the agent. /evolve runs it before and after mutating.

  python3 scripts/doctor.py          # report; exit 1 on errors
  python3 scripts/doctor.py --json   # machine-readable metrics for EVOLUTION.md comparisons

Errors break things (bad frontmatter, dangling references, malformed lessons).
Metrics track cost and health over generations (context spent on skill descriptions, lesson stats).
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"
sys.path.insert(0, str(ROOT / "scripts"))
from import_sources import frontmatter  # noqa: E402

errors, warnings, m = [], [], {}

# --- skills -----------------------------------------------------------------
vendored = {l.split("\t")[0] for l in (SKILLS / ".vendored").read_text().splitlines()} if (SKILLS / ".vendored").exists() else set()
desc_chars, own, long_desc = 0, 0, []
for f in sorted(SKILLS.glob("*/SKILL.md")):
    d = f.parent.name
    fm = frontmatter(f.read_text(errors="replace"))
    if not fm.get("name") or not fm.get("description"):
        errors.append(f"{d}: SKILL.md frontmatter needs name and description")
        continue
    desc_chars += len(fm["description"])
    if d not in vendored:
        own += 1
        if len(fm["description"]) > 200:
            long_desc.append(d)
    body = f.read_text(errors="replace")
    if "superpowers:" in body:
        errors.append(f"{d}: dangling 'superpowers:' reference")
    for ref in set(re.findall(r"`((?:scripts|memory|catalog|research)/[\w./-]+\.(?:py|sh|md|log|tsv))`", body)):
        if not (f.parent / ref).exists() and not (ROOT / ref).exists() \
                and not ref.startswith(("memory/skill-usage", "catalog/INDEX")):
            warnings.append(f"{d}: references missing file {ref}")
m["skills_total"] = len(list(SKILLS.glob("*/SKILL.md")))
m["skills_own"] = own
m["skills_vendored"] = m["skills_total"] - own
m["skill_description_chars"] = desc_chars  # loaded into every session
if long_desc:
    warnings.append(f"own skills with descriptions > 200 chars (route on the first ~60): {', '.join(long_desc)}")

# --- lessons ----------------------------------------------------------------
lines = (ROOT / "memory" / "learnings.md").read_text().splitlines()
lessons = [l for l in lines if l.startswith("- ")]
bad = [l[:60] for l in lessons if not re.match(r"^- \[(0\.\d|1\.0)\] \d{4}-\d{2}-\d{2} — .+", l)]
for b in bad:
    errors.append(f"malformed lesson: {b}")
conf = [float(x) for x in re.findall(r"^- \[([\d.]+)\]", "\n".join(lessons), re.M)]
m["lessons"] = len(lessons)
m["lessons_injected"] = sum(c >= 0.7 for c in conf)
m["lessons_mean_confidence"] = round(sum(conf) / len(conf), 2) if conf else 0
if len(lines) > 60:
    errors.append(f"memory/learnings.md has {len(lines)} lines (limit 60)")
if any(c < 0.3 for c in conf):
    warnings.append("lessons below 0.3 confidence should be dropped")

# --- logs and loop state ----------------------------------------------------
fl = ROOT / "memory" / "failures.log"
m["unprocessed_failures"] = len(fl.read_text().splitlines()) if fl.exists() else 0
su = ROOT / "memory" / "skill-usage.log"
m["skill_uses_logged"] = len(su.read_text().splitlines()) if su.exists() else 0
ev = (ROOT / "EVOLUTION.md").read_text()
gens = re.findall(r"^## Generation (\d+)", ev, re.M)
m["generation"] = int(gens[-1]) if gens else 0
if gens and "Hypothesis:" not in ev[ev.rindex("## Generation"):]:
    errors.append("latest EVOLUTION.md generation has no Hypothesis")

# --- hooks --------------------------------------------------------------------
settings = json.loads((ROOT / ".claude" / "settings.json").read_text())
for s in set(re.findall(r"scripts/[\w]+\.(?:sh|py)", json.dumps(settings))):
    if not (ROOT / s).exists():
        errors.append(f"hook script missing: {s}")
m["hook_events"] = len(settings.get("hooks", {}))
m["catalog_entries"] = max(0, len((ROOT / "catalog" / "INDEX.tsv").read_text().splitlines()) - 1) if (ROOT / "catalog" / "INDEX.tsv").exists() else 0

if "--json" in sys.argv:
    print(json.dumps({"metrics": m, "errors": errors, "warnings": warnings}, indent=2))
else:
    for k, v in m.items():
        print(f"{k:<28} {v}")
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print("healthy" if not errors else f"{len(errors)} error(s)")
sys.exit(1 if errors else 0)
