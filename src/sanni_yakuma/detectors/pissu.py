"""Pissu Sanniya (temporary madness) -> magic madness: hard-coded numbers, paths, hosts."""

import re

from ..omen import Evidence, Omen
from ..repo import Repo
from .base import MAX_EVIDENCE, severity, snippet

ABS_PATH = re.compile(r"""["'](/Users/[^"']+|/home/[^"']+|[A-Za-z]:\\\\[^"']+|/var/www/[^"']*)["']""")
LOCAL_URL = re.compile(
    r"""["'](https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+)[^"']*)["']"""
)
STRING = re.compile(r"""(["'])(?:\\.|(?!\1).)*\1""")
NUMBER = re.compile(r"(?<![\w.#$])(\d+\.\d+|\d{2,})(?![\w.])")
COMMENT = re.compile(r"^\s*(#|//|/\*|\*|--)")
CONSTANT_LINE = re.compile(
    r"^\s*(export\s+)?((public|private|protected|static|final|const|readonly)\s+)*[A-Z][A-Z0-9_]*\s*(:[^=]+)?="
    r"|^\s*(const|final|static final|#define|enum)\b"
    r"|^\s*[A-Z][A-Z0-9_]+\s*="
)
IGNORE_LINE = re.compile(
    r"^\s*(import|from|#include|using|package|@|version|case\b)|\b(range|sleep|timeout|port|status|assert|expect)\b",
    re.IGNORECASE,
)
HARMLESS = {
    "10",
    "16",
    "24",
    "32",
    "60",
    "64",
    "90",
    "100",
    "128",
    "180",
    "200",
    "201",
    "204",
    "255",
    "256",
    "360",
    "400",
    "401",
    "403",
    "404",
    "500",
    "1000",
    "1024",
    "0.5",
    "1.0",
    "2.0",
    "0.0",
}


def magic_numbers(line: str) -> list[str]:
    if COMMENT.match(line) or CONSTANT_LINE.match(line) or IGNORE_LINE.search(line):
        return []
    code = STRING.sub('""', line.split("//")[0].split(" #")[0])
    return [n for n in NUMBER.findall(code) if n not in HARMLESS and not re.fullmatch(r"(19|20)\d\d", n)]


def detect(repo: Repo) -> Omen:
    paths, hosts, magic = [], [], []
    total_lines = 0
    for path in repo.source_files:
        lines = repo.lines(path)
        total_lines += len(lines)
        css_like = path.endswith((".vue", ".svelte"))
        in_docstring = False
        for number, line in enumerate(lines, start=1):
            # Numbers in docstrings and other triple-quoted text are prose, not magic.
            quotes = line.count('"""') + line.count("'''")
            if in_docstring or quotes:
                if quotes % 2:
                    in_docstring = not in_docstring
                continue
            if len(line) > 400:
                continue
            if m := ABS_PATH.search(line):
                paths.append(
                    Evidence(path=path, line=number, snippet=snippet(line), note=f"hard-coded path {m.group(1)[:40]}")
                )
            if m := LOCAL_URL.search(line):
                hosts.append(Evidence(path=path, line=number, snippet=snippet(line), note="hard-coded local address"))
            if not css_like and (found := magic_numbers(line)):
                magic.append(
                    Evidence(path=path, line=number, snippet=snippet(line), note="magic number " + ", ".join(found[:3]))
                )

    per_kloc = len(magic) / (total_lines / 1000) if total_lines else 0.0
    sev_magic = min(
        severity(len(magic), mild=20, clear=60, severe=150), severity(per_kloc, mild=15, clear=30, severe=60)
    )
    sev = max(
        sev_magic, severity(len(paths), mild=1, clear=3, severe=8), severity(len(hosts), mild=2, clear=6, severe=15)
    )
    evidence = (
        paths[:5] + hosts[:4] + (magic[: MAX_EVIDENCE - min(len(paths), 5) - min(len(hosts), 4)] if sev_magic else [])
    )
    return Omen(
        demon="Pissu",
        sickness="magic madness",
        found=sev > 0,
        severity_hint=sev,
        summary=(
            f"{len(magic)} magic-number lines ({per_kloc:.0f} per 1,000), "
            f"{len(paths)} hard-coded paths, {len(hosts)} hard-coded local hosts."
        ),
        metrics={
            "magic_lines": len(magic),
            "magic_per_kloc": round(per_kloc, 1),
            "hardcoded_paths": len(paths),
            "local_hosts": len(hosts),
        },
        evidence=evidence if sev else [],
    )
