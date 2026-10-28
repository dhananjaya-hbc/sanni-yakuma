"""Bihiri Sanniya (deafness) -> swallowed errors the code never hears."""

import re

from ..omen import Evidence, Omen
from ..repo import Repo
from .base import MAX_EVIDENCE, severity, snippet

PY_BARE_EXCEPT = re.compile(r"^\s*except\s*:")
PY_EXCEPT = re.compile(r"^\s*except\b.*:\s*(#.*)?$")
PY_SILENT_BODY = re.compile(r"^\s*(pass|\.\.\.)\s*(#.*)?$")
PY_SILENT_INLINE = re.compile(r"^\s*except\b.*:\s*(pass|\.\.\.)\s*(#.*)?$")
# `try: import x / except ImportError: pass` is the normal optional-import idiom.
PY_OPTIONAL_IMPORT = re.compile(r"^\s*except\s*\(?\s*(ImportError|ModuleNotFoundError)\b")

# catch (e) {}   catch {}   .catch(() => {})   .catch(function () {})
C_EMPTY_CATCH = re.compile(r"catch\s*(\([^)]*\))?\s*\{\s*\}")
JS_EMPTY_PROMISE_CATCH = re.compile(r"\.catch\(\s*(\([^)]*\)|\w+)?\s*(=>)?\s*(function\s*\([^)]*\))?\s*\{\s*\}\s*\)")
C_CATCH_OPEN = re.compile(r"catch\s*(\([^)]*\))?\s*\{\s*(//.*)?$")
C_LIKE_EXTS = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".java", ".kt", ".cs",
               ".php", ".swift", ".scala", ".dart", ".cpp", ".cc", ".vue", ".svelte")


def next_code_line(lines: list[str], start: int) -> str | None:
    for line in lines[start:]:
        if line.strip():
            return line
    return None


def scan_python(path: str, lines: list[str]) -> list[Evidence]:
    found = []
    for i, line in enumerate(lines):
        if PY_OPTIONAL_IMPORT.match(line):
            continue
        if PY_BARE_EXCEPT.match(line):
            found.append(Evidence(path=path, line=i + 1, snippet=snippet(line), note="bare except"))
        elif PY_SILENT_INLINE.match(line):
            found.append(Evidence(path=path, line=i + 1, snippet=snippet(line), note="error silenced"))
        elif PY_EXCEPT.match(line):
            body = next_code_line(lines, i + 1)
            if body is not None and PY_SILENT_BODY.match(body):
                found.append(Evidence(path=path, line=i + 1, snippet=f"{line.strip()} {body.strip()}", note="error silenced"))
    return found


def scan_c_like(path: str, lines: list[str]) -> list[Evidence]:
    found = []
    for i, line in enumerate(lines):
        if C_EMPTY_CATCH.search(line) or JS_EMPTY_PROMISE_CATCH.search(line):
            found.append(Evidence(path=path, line=i + 1, snippet=snippet(line), note="empty catch"))
        elif C_CATCH_OPEN.search(line):
            body = next_code_line(lines, i + 1)
            if body is not None and body.strip().startswith("}"):
                found.append(Evidence(path=path, line=i + 1, snippet=snippet(line), note="empty catch"))
    return found


def detect(repo: Repo) -> Omen:
    hits: list[Evidence] = []
    for path in repo.source_files:
        if path.endswith(".py"):
            hits.extend(scan_python(path, repo.lines(path)))
        elif path.endswith(C_LIKE_EXTS):
            hits.extend(scan_c_like(path, repo.lines(path)))
    bare = sum(1 for h in hits if h.note == "bare except")
    sev = severity(len(hits), mild=1, clear=4, severe=12)
    return Omen(
        demon="Bihiri", sickness="swallowed errors", found=sev > 0, severity_hint=sev,
        summary=f"{len(hits)} places where errors are caught and ignored." if hits else "No swallowed errors found.",
        metrics={"total": len(hits), "bare_except": bare, "files": len({h.path for h in hits})},
        evidence=hits[:MAX_EVIDENCE],
    )
