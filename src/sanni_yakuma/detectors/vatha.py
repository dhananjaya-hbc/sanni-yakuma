"""Vatha Sanniya (bloating, wind) -> dependency bloat."""

from ..omen import Evidence, Omen
from ..repo import Repo
from .base import severity
from .manifests import find_manifests

# Packages that famously do one line of work.
TRIVIAL = {"left-pad", "is-odd", "is-even", "is-number", "is-array", "isarray", "is-string", "is-object",
           "is-positive", "is-negative", "is-true", "is-false", "pad-left", "array-first", "is-thirteen"}


def detect(repo: Repo) -> Omen:
    manifests = find_manifests(repo)
    runtime = {name for m in manifests for name in m.deps}
    dev = {name for m in manifests for name in m.dev} - runtime
    own_lines = sum(1 for f in repo.source_files for line in repo.lines(f) if line.strip())
    total = len(runtime) + len(dev)
    per_kloc = total / max(own_lines / 1000, 0.5)  # floor at 500 lines so tiny repos are not judged harshly
    trivial = sorted((runtime | dev) & TRIVIAL)

    sev = severity(per_kloc, mild=20, clear=40, severe=80) if total >= 15 else 0
    if total >= 150:
        sev = max(sev, 2)
    if trivial:
        sev = max(sev, 1)
    evidence = []
    if sev:
        biggest = max(manifests, key=lambda m: m.total)
        evidence.append(Evidence(path=biggest.path, note=f"{len(biggest.deps)} dependencies + {len(biggest.dev)} dev dependencies"))
        evidence.append(Evidence(note=f"{total} dependencies for {own_lines:,} lines of own code ({per_kloc:.0f} per 1,000 lines)"))
        evidence += [Evidence(snippet=name, note="a whole package for one line of code") for name in trivial]
    return Omen(
        demon="Vatha", sickness="dependency bloat", found=sev > 0, severity_hint=sev,
        summary=f"{total} dependencies ({len(runtime)} runtime, {len(dev)} dev) for {own_lines:,} lines of own code.",
        metrics={"runtime_deps": len(runtime), "dev_deps": len(dev), "own_lines": own_lines,
                 "deps_per_kloc": round(per_kloc, 1), "trivial_packages": len(trivial)},
        evidence=evidence,
    )
