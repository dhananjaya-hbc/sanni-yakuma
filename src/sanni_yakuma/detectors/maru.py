"""Maru Sanniya (delirium, death) -> dead code left lying in the comments."""

import re
from pathlib import PurePosixPath

from ..omen import Evidence, Omen
from ..repo import Repo
from .base import MAX_EVIDENCE, severity, snippet

HASH_COMMENT = {".py", ".rb", ".sh"}
MIN_BLOCK = 5
CODE_LIKE = re.compile(
    r"""(;\s*$|[{}]\s*$|\)\s*:?\s*$|^\s*(def|class|import|from|return|if|elif|else|for|while|try|except|"""
    r"""function|const|let|var|public|private|static|func|fn|print|console\.|self\.|this\.)\b|^\s*[\w.\[\]'"]+\s*[+\-*/]?=\s*\S)"""
)
PROSE = re.compile(r"^[A-Za-z][\w'’,-]*( [A-Za-z][\w'’,-]*){5,}[.!?:]?$")


def comment_body(line: str, marker: str) -> str | None:
    stripped = line.strip()
    if not stripped.startswith(marker):
        return None
    body = stripped[len(marker):]
    return body[1:] if body.startswith(" ") else body


def looks_like_code(body: str) -> bool:
    body = body.strip()
    return bool(body) and not PROSE.match(body) and bool(CODE_LIKE.search(body))


def dead_blocks(lines: list[str], marker: str) -> list[tuple[int, int, str]]:
    """(start line, length, first line) of commented-out code runs."""
    blocks, run = [], []
    for number, line in enumerate(lines + [""], start=1):
        body = comment_body(line, marker)
        if body is not None and not body.lstrip().startswith(("!", "-*-", "noqa", "type:", "eslint", "@")):
            run.append((number, body))
            continue
        if len(run) >= MIN_BLOCK:
            code = sum(looks_like_code(b) for _, b in run)
            if code / len(run) >= 0.6:
                first = next(b for _, b in run if looks_like_code(b))
                blocks.append((run[0][0], len(run), first))
        run = []
    return blocks


def detect(repo: Repo) -> Omen:
    found = []
    for path in repo.source_files:
        marker = "#" if PurePosixPath(path).suffix in HASH_COMMENT else "//"
        found += [(path, *block) for block in dead_blocks(repo.lines(path), marker)]

    dead_lines = sum(length for _, _, length, _ in found)
    found.sort(key=lambda b: b[2], reverse=True)
    sev = max(severity(len(found), mild=2, clear=6, severe=15), severity(dead_lines, mild=10, clear=50, severe=150))
    return Omen(
        demon="Maru", sickness="dead code", found=sev > 0, severity_hint=sev,
        summary=f"{dead_lines} lines of commented-out code in {len(found)} blocks." if found else "No corpses in the comments.",
        metrics={"blocks": len(found), "dead_lines": dead_lines},
        evidence=[Evidence(path=p, line=start, snippet=snippet(first), note=f"{length} commented-out lines")
                  for p, start, length, first in found[:MAX_EVIDENCE]] if sev else [],
    )
