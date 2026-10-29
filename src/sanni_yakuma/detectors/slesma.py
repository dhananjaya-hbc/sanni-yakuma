"""Slesma Sanniya (phlegm) -> the clogged repo: junk, binaries, huge files."""

from pathlib import Path

from ..omen import Evidence, Omen
from ..repo import Repo, is_test_path
from .base import MAX_EVIDENCE

JUNK_DIRS = {
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".mypy_cache",
    "bower_components",
    ".next",
    ".nuxt",
}
JUNK_NAMES = {".DS_Store", "Thumbs.db", ".env", "desktop.ini"}
BINARY_EXTS = {
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".o",
    ".a",
    ".pyc",
    ".class",
    ".jar",
    ".war",
    ".zip",
    ".tar",
    ".gz",
    ".tgz",
    ".rar",
    ".7z",
    ".whl",
    ".egg",
    ".apk",
    ".dmg",
    ".iso",
    ".bin",
}
HUGE_BYTES = 1_000_000


def detect(repo: Repo) -> Omen:
    gitignore = repo.exists(".gitignore")
    junk_dirs: dict[str, int] = {}
    junk_files, binaries, huge = [], [], []
    for path in repo.files:
        p = Path(path)
        hit = next((part for part in p.parts[:-1] if part in JUNK_DIRS), None)
        if hit:
            junk_dirs[hit] = junk_dirs.get(hit, 0) + 1
            continue
        if p.name in JUNK_NAMES:
            junk_files.append(path)
        elif is_test_path(path):  # archives and big files in tests are fixtures on purpose
            continue
        elif p.suffix.lower() in BINARY_EXTS:
            binaries.append(path)
        elif repo.size(path) > HUGE_BYTES:
            huge.append(path)

    evidence: list[Evidence] = []
    if not gitignore:
        evidence.append(Evidence(note="No .gitignore at the repository root"))
    for name, count in junk_dirs.items():
        evidence.append(Evidence(path=f"{name}/", note=f"{count} files committed from {name}/"))
    evidence += [Evidence(path=f, note="should never be committed") for f in junk_files]
    evidence += [Evidence(path=f, note="compiled or archive file") for f in binaries]
    evidence += [
        Evidence(path=f, note=f"{repo.size(f) / 1e6:.1f} MB") for f in sorted(huge, key=repo.size, reverse=True)
    ]

    clogs = len(junk_dirs) + len(junk_files) + len(binaries) + len(huge)
    if junk_dirs or ".env" in {Path(f).name for f in junk_files}:
        sev = 3
    elif clogs >= 5 or (not gitignore and clogs):
        sev = 2
    elif clogs or not gitignore:
        sev = 1
    else:
        sev = 0
    return Omen(
        demon="Slesma",
        sickness="clogged repo",
        found=sev > 0,
        severity_hint=sev,
        summary=f"{clogs} clog(s)" + ("" if gitignore else " and no .gitignore") + "."
        if sev
        else "Clean: .gitignore present, no junk committed.",
        metrics={
            "gitignore": gitignore,
            "junk_dirs": len(junk_dirs),
            "junk_files": len(junk_files),
            "binaries": len(binaries),
            "huge_files": len(huge),
        },
        evidence=evidence[:MAX_EVIDENCE],
    )
