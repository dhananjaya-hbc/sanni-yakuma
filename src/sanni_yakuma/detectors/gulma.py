"""Gulma Sanniya (worms) -> hidden worms: TODO, FIXME, HACK, XXX."""

import re
from collections import Counter

from ..omen import Omen
from ..repo import Repo
from .base import MAX_EVIDENCE, grep, severity

# Only markers that start a comment: "# TODO", "// FIXME:", "/* HACK", "<!-- XXX".
WORM_RE = re.compile(r"(?:#|//|/\*|\*|<!--|--)\s*(TODO|FIXME|HACK|XXX)\b")


def detect(repo: Repo) -> Omen:
    hits = list(grep(repo, repo.source_files, WORM_RE))
    kinds = Counter(WORM_RE.search(h.snippet).group(1) for h in hits)
    # The angrier markers are worse than a polite to-do, so show them first.
    hits.sort(key=lambda h: WORM_RE.search(h.snippet).group(1) in {"TODO"})
    sev = severity(len(hits), mild=5, clear=20, severe=60)
    return Omen(
        demon="Gulma", sickness="hidden worms", found=sev > 0, severity_hint=sev,
        summary=f"{len(hits)} worm marker(s): " + ", ".join(f"{n} {k}" for k, n in kinds.most_common()) if hits else "No TODO/FIXME/HACK markers.",
        metrics={"total": len(hits), **{k.lower(): n for k, n in kinds.items()},
                 "files": len({h.path for h in hits})},
        evidence=hits[:MAX_EVIDENCE],
    )
