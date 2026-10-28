"""Butha Sanniya (madness caused by spirits) -> dependency hell.

Outside spirits (other people's packages) drive the repo mad when nothing pins them down.
"""

from ..omen import Evidence, Omen
from ..repo import Repo
from .base import MAX_EVIDENCE
from .manifests import Manifest, find_manifests, has_lockfile

ALWAYS_LOOSE = {"*", "latest", "x", "next"}
# Libraries in these ecosystems publish version ranges on purpose and do not commit lockfiles.
LOCK_OPTIONAL = {"python", "rust"}


def needs_lockfile(repo: Repo, ecosystem: str) -> bool:
    if ecosystem in LOCK_OPTIONAL:
        return False
    if ecosystem == "ruby":  # gems ship a .gemspec and leave Gemfile.lock out
        return not any(f.endswith(".gemspec") for f in repo.files)
    return True


def pins_expected(manifest: Manifest) -> bool:
    """Apps pin versions; library metadata (pyproject, Cargo) may list bare names."""
    if manifest.ecosystem == "go":
        return False
    return manifest.ecosystem not in LOCK_OPTIONAL or manifest.path.endswith(".txt")


def detect(repo: Repo) -> Omen:
    evidence: list[Evidence] = []
    no_lock, loose_total, wild = [], 0, 0
    for manifest in find_manifests(repo):
        if manifest.total == 0 or manifest.path.startswith(("docs/", "doc/")):
            continue
        locked = has_lockfile(repo, manifest)
        if not locked and needs_lockfile(repo, manifest.ecosystem):
            no_lock.append(manifest)
            evidence.append(Evidence(path=manifest.path, note=f"{manifest.total} {manifest.ecosystem} dependencies and no lockfile"))
        for name, spec in {**manifest.deps, **manifest.dev}.items():
            if spec.strip().lower() in ALWAYS_LOOSE:
                wild += 1
                evidence.append(Evidence(path=manifest.path, snippet=f'"{name}": "{spec}"', note="any version at all"))
            elif not locked and not spec.strip() and pins_expected(manifest):
                loose_total += 1
                if loose_total <= 5:
                    evidence.append(Evidence(path=manifest.path, snippet=f"{name} {spec or '(no version)'}".strip(), note="no version at all"))

    if (no_lock and loose_total >= 5) or wild >= 3:
        sev = 3
    elif no_lock or wild:
        sev = 2
    elif loose_total:
        sev = 1
    else:
        sev = 0
    return Omen(
        demon="Butha", sickness="dependency hell", found=sev > 0, severity_hint=sev,
        summary=(f"{len(no_lock)} manifest(s) without a lockfile, {loose_total} unpinned and {wild} wildcard dependencies."
                 if sev else "Dependencies are pinned or locked."),
        metrics={"manifests_without_lock": len(no_lock), "unpinned": loose_total, "wildcards": wild},
        evidence=evidence[:MAX_EVIDENCE],
    )
