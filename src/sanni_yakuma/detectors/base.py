"""Helpers shared by the detectors."""

import re
from collections.abc import Iterable, Iterator

from ..omen import Evidence
from ..repo import Repo

MAX_EVIDENCE = 12
SNIPPET_LEN = 160


def snippet(line: str) -> str:
    line = line.strip()
    return line if len(line) <= SNIPPET_LEN else line[: SNIPPET_LEN - 1] + "…"


def grep(repo: Repo, files: Iterable[str], pattern: re.Pattern) -> Iterator[Evidence]:
    """Yield one Evidence per matching line."""
    for path in files:
        for number, line in enumerate(repo.lines(path), start=1):
            if pattern.search(line):
                yield Evidence(path=path, line=number, snippet=snippet(line))


def severity(value: float, mild: float, clear: float, severe: float) -> int:
    """Map a number onto the 0-3 severity scale using three thresholds."""
    if value >= severe:
        return 3
    if value >= clear:
        return 2
    if value >= mild:
        return 1
    return 0
