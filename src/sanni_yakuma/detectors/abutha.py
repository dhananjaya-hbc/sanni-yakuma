"""Abutha Sanniya (madness not caused by spirits) -> self-made complexity.

Nobody cursed this code; its own authors made it mad, one more `if` at a time.
"""

import re
from collections import Counter

import lizard

from ..omen import Evidence, Omen
from ..repo import Repo
from .base import MAX_EVIDENCE, severity

LONG_NLOC = 60
HIGH_CCN = 15
DEEP_NESTING = 4
MAX_FILE_BYTES = 300_000
MAX_FILES = 2000


def indent_width(line: str) -> int:
    expanded = line.expandtabs(4)
    return len(expanded) - len(expanded.lstrip())


def indent_unit(lines: list[str]) -> int:
    """The file's usual indent step: 2 or 4 spaces."""
    steps: Counter[int] = Counter()
    previous = 0
    for line in lines:
        if not line.strip():
            continue
        width = indent_width(line)
        if width > previous:
            steps[width - previous] += 1
        previous = width
    common = steps.most_common(1)
    return 2 if common and common[0][0] == 2 else 4


# Lines that open a block. Object/dict literals and comments do not count.
PY_OPENER = re.compile(r":\s*(#.*)?$")
C_OPENER = re.compile(r"\{\s*$")
LITERAL = re.compile(r"([=(,:\[]|return|=>)\s*\{\s*$")
COMMENT = re.compile(r"^\s*(#|//|/?\*)")


def nesting_depth(lines: list[str], start: int, end: int, unit: int, python: bool) -> int:
    """Levels of blocks nested inside a function body, judged by the indentation of block openers."""
    body = [line for line in lines[start - 1 : end] if line.strip() and not COMMENT.match(line)]
    if len(body) < 2:
        return 0
    base = indent_width(body[0])
    if python:
        openers = [line for line in body[1:] if PY_OPENER.search(line)]
    else:
        openers = [line for line in body[1:] if C_OPENER.search(line) and not LITERAL.search(line)]
    if not openers:
        return 0
    return max(0, (max(indent_width(line) for line in openers) - base) // unit)


def detect(repo: Repo) -> Omen:
    possessed = []
    analysed = 0
    for path in repo.source_files[:MAX_FILES]:
        if repo.size(path) > MAX_FILE_BYTES or path.endswith((".sh", ".vue", ".svelte")):
            continue
        text = repo.read_text(path)
        if text is None:
            continue
        try:
            info = lizard.analyze_file.analyze_source_code(path, text)
        except Exception:  # lizard can choke on unusual syntax; skip that file, not the ritual
            continue
        lines = text.splitlines()
        unit = indent_unit(lines)
        for fn in info.function_list:
            analysed += 1
            depth = nesting_depth(lines, fn.start_line, fn.end_line, unit, path.endswith(".py"))
            if fn.nloc >= LONG_NLOC or fn.cyclomatic_complexity >= HIGH_CCN or depth >= DEEP_NESTING:
                possessed.append((fn, path, depth))

    worst = sorted(possessed, key=lambda p: p[0].cyclomatic_complexity + p[0].nloc / 10 + p[2] * 3, reverse=True)
    sev = severity(len(possessed), mild=3, clear=10, severe=25)
    if worst and (worst[0][0].cyclomatic_complexity >= 40 or worst[0][0].nloc >= 200):
        sev = max(sev, 2)
    evidence = [
        Evidence(
            path=path,
            line=fn.start_line,
            note=f"`{fn.name}`: {fn.nloc} lines, complexity {fn.cyclomatic_complexity}, nesting {depth}",
        )
        for fn, path, depth in worst[:MAX_EVIDENCE]
    ]
    return Omen(
        demon="Abutha",
        sickness="self-made complexity",
        found=sev > 0,
        severity_hint=sev,
        summary=f"{len(possessed)} of {analysed} functions are long, tangled or deeply nested."
        if possessed
        else f"All {analysed} functions are reasonably sane.",
        metrics={
            "functions": analysed,
            "possessed": len(possessed),
            "max_complexity": max((fn.cyclomatic_complexity for fn, _, _ in possessed), default=0),
            "max_nloc": max((fn.nloc for fn, _, _ in possessed), default=0),
        },
        evidence=evidence if sev else [],
    )
