"""Golu Sanniya (muteness) -> the silent repo: no README, few docstrings."""

import ast
import re

from ..omen import Evidence, Omen
from ..repo import Repo

README_RE = re.compile(r"^readme(\.[a-z]+)?$", re.IGNORECASE)
THIN_README_WORDS = 150


def docstring_coverage(repo: Repo) -> tuple[int, int, list[Evidence]]:
    """(documented, total, examples of undocumented) for public Python defs."""
    documented = total = 0
    missing: list[Evidence] = []
    for path in repo.source_files:
        if not path.endswith(".py"):
            continue
        text = repo.read_text(path)
        if text is None:
            continue
        try:
            tree = ast.parse(text)
        except (SyntaxError, ValueError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if node.name.startswith("_"):
                continue
            total += 1
            if ast.get_docstring(node):
                documented += 1
            elif len(missing) < 5:
                missing.append(Evidence(path=path, line=node.lineno, note=f"`{node.name}` has no docstring"))
    return documented, total, missing


def detect(repo: Repo) -> Omen:
    readmes = [f for f in repo.files if "/" not in f and README_RE.match(f)]
    words = len((repo.read_text(readmes[0]) or "").split()) if readmes else 0
    documented, total, missing = docstring_coverage(repo)
    coverage = documented / total if total else None

    evidence: list[Evidence] = []
    if not readmes:
        evidence.append(Evidence(note="No README at the repository root"))
        sev = 3
    elif words < THIN_README_WORDS:
        evidence.append(Evidence(path=readmes[0], note=f"README has only {words} words"))
        sev = 2
    else:
        sev = 0
    if coverage is not None and total >= 10 and coverage < 0.2:
        evidence.extend(missing)
        sev = max(sev, 1)

    if not readmes:
        summary = "The repo has no README; it cannot speak for itself."
    elif sev:
        summary = f"README has {words} words; docstring coverage {coverage:.0%}." if coverage is not None else f"README has only {words} words."
    else:
        summary = f"README has {words} words."
    return Omen(
        demon="Golu", sickness="silent repo", found=sev > 0, severity_hint=sev,
        summary=summary,
        metrics={"readme": readmes[0] if readmes else None, "readme_words": words,
                 "python_defs": total, "docstring_coverage": round(coverage, 2) if coverage is not None else None},
        evidence=evidence,
    )
