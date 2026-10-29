"""Deva Sanniya (epidemics) -> copy-paste spreading from file to file."""

import hashlib
import re
from collections import defaultdict

from ..omen import Evidence, Omen
from ..repo import Repo
from .base import MAX_EVIDENCE, severity

WINDOW = 6
MIN_CHARS = 150
MAX_FILES = 3000
GENERATED_MIN_WINDOWS = 100
TRIVIAL = re.compile(
    r"^(import |from \S+ import|#include|using |require\(|package |[})\]];?,?$|end$|else:?$|\*|//|#|/\*|\"\"\"|''')"
)


def code_lines(lines: list[str]) -> list[tuple[int, str]]:
    """(original line number, normalised text) for lines that carry real code."""
    kept = []
    for number, line in enumerate(lines, start=1):
        text = " ".join(line.split())
        if len(text) > 3 and not TRIVIAL.match(text):
            kept.append((number, text))
    return kept


def windows(lines: list[str]) -> list[tuple[str, int]]:
    """(digest, start line) for each substantial window; overlapping repeats in one file count once."""
    kept = code_lines(lines)
    found, last_seen = [], {}
    for i in range(len(kept) - WINDOW + 1):
        block = "\n".join(text for _, text in kept[i : i + WINDOW])
        if len(block) < MIN_CHARS:
            continue
        digest = hashlib.blake2b(block.encode(), digest_size=12).hexdigest()
        if digest in last_seen and i - last_seen[digest] <= WINDOW:
            continue
        last_seen[digest] = i
        found.append((digest, kept[i][0]))
    return found


def generated_copies(per_file: dict[str, list[tuple[str, int]]], owners: dict[str, set[str]]) -> set[str]:
    """Big files that mostly repeat other files: build bundles, not copy-paste."""
    copies = set()
    for path, wins in per_file.items():
        if len(wins) < GENERATED_MIN_WINDOWS:
            continue
        shared = sum(1 for digest, _ in wins if len(owners[digest]) > 1)
        if shared / len(wins) >= 0.5:
            copies.add(path)
    return copies


def detect(repo: Repo) -> Omen:
    per_file = {path: windows(repo.lines(path)) for path in repo.source_files[:MAX_FILES]}
    owners: dict[str, set[str]] = defaultdict(set)
    for path, wins in per_file.items():
        for digest, _ in wins:
            owners[digest].add(path)
    bundles = generated_copies(per_file, owners)

    seen: dict[str, list[tuple[str, int]]] = defaultdict(list)
    total_lines = 0
    for path, wins in per_file.items():
        if path in bundles:
            continue
        total_lines += len(code_lines(repo.lines(path)))
        for digest, line in wins:
            seen[digest].append((path, line))

    clones = [locs for locs in seen.values() if len(locs) > 1]
    # Merge runs: a 20-line clone shows up as many overlapping windows.
    reported: set[tuple[str, int]] = set()
    groups = []
    for locs in sorted(clones, key=len, reverse=True):
        if any((p, ln + d) in reported for p, ln in locs for d in range(-WINDOW * 2, WINDOW * 2)):
            continue
        reported.update(locs)
        groups.append(locs)

    duplicated = sum(len(locs) - 1 for locs in groups) * WINDOW
    share = duplicated / total_lines if total_lines else 0.0
    sev = min(severity(len(groups), mild=3, clear=10, severe=30), severity(share, mild=0.02, clear=0.05, severe=0.12))
    evidence = []
    for locs in groups[:MAX_EVIDENCE]:
        (path, line), others = locs[0], locs[1:]
        also = ", ".join(f"{p}:{ln}" for p, ln in others[:3]) + (
            f" and {len(others) - 3} more" if len(others) > 3 else ""
        )
        evidence.append(Evidence(path=path, line=line, note=f"same {WINDOW}+ lines also at {also}"))
    summary = f"{len(groups)} copied blocks, about {share:.0%} of the code." if groups else "No copy-paste epidemic."
    if bundles:
        summary += f" ({len(bundles)} generated bundle(s) ignored.)"
    return Omen(
        demon="Deva",
        sickness="copy-paste spreading",
        found=sev > 0,
        severity_hint=sev,
        summary=summary,
        metrics={
            "clone_groups": len(groups),
            "duplicated_lines": duplicated,
            "share": round(share, 3),
            "generated_copies": len(bundles),
        },
        evidence=evidence if sev else [],
    )
