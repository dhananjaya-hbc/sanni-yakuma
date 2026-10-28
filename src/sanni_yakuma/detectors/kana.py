"""Kana Sanniya (blindness) -> no tests, so nobody can see if the code works."""

from ..omen import Evidence, Omen
from ..repo import Repo
from .base import severity


def detect(repo: Repo) -> Omen:
    sources, tests = len(repo.source_files), len(repo.test_files)
    if sources == 0:
        return Omen(demon="Kana", sickness="can't see if it works", found=False, severity_hint=0,
                    summary="No source files to test.", metrics={"source_files": 0, "test_files": tests})

    ratio = tests / sources
    if tests == 0:
        sev = 3 if sources >= 3 else 2
        evidence = [Evidence(note=f"{sources} source files and not a single test file")]
    else:
        # Fewer than one test file per 10 source files is mild blindness.
        sev = severity(1 / ratio, mild=5, clear=10, severe=25) if sources >= 10 else 0
        evidence = [Evidence(path=t, note="test file") for t in repo.test_files[:3]] if sev else []
    return Omen(
        demon="Kana", sickness="can't see if it works", found=sev > 0, severity_hint=sev,
        summary=f"{tests} test files for {sources} source files.",
        metrics={"source_files": sources, "test_files": tests, "test_ratio": round(ratio, 3)},
        evidence=evidence,
    )
