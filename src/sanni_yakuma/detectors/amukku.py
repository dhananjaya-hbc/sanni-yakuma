"""Amukku Sanniya (vomiting) -> log vomit: debug prints all over the code."""

import re
from collections import Counter

from ..omen import Evidence, Omen
from ..repo import Repo
from .base import severity, snippet

# Debug output calls per language. Logging frameworks are fine; these are not.
VOMIT = {
    ".py": re.compile(r"^\s*(print\s*\(|pprint\s*\(|breakpoint\s*\(\))"),
    ".js": re.compile(r"\bconsole\.(log|debug|dir|trace)\s*\(|^\s*debugger\s*;?\s*$"),
    ".go": re.compile(r"\bfmt\.Print(ln|f)?\s*\("),
    ".java": re.compile(r"\bSystem\.(out|err)\.print(ln|f)?\s*\(|\.printStackTrace\s*\(\s*\)"),
    ".rb": re.compile(r"^\s*(puts|p|pp)\s"),
    ".php": re.compile(r"\b(var_dump|print_r|dd)\s*\("),
    ".rs": re.compile(r"\b(println!|dbg!|eprintln!)\s*\("),
    ".cs": re.compile(r"\bConsole\.Write(Line)?\s*\("),
}
for ext in (".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte"):
    VOMIT[ext] = VOMIT[".js"]
VOMIT[".kt"] = re.compile(r"^\s*println\s*\(|\.printStackTrace\s*\(\s*\)")

# Entry points and CLIs are supposed to print.
CLI_HINTS = re.compile(r"(^|/)(cli|__main__|main|cmd|bin|scripts?|examples?|demo)(/|\.|$)", re.IGNORECASE)


def detect(repo: Repo) -> Omen:
    per_file: Counter[str] = Counter()
    samples: dict[str, Evidence] = {}
    total_lines = 0
    for path in repo.source_files:
        pattern = VOMIT.get("." + path.rsplit(".", 1)[-1].lower())
        if pattern is None or CLI_HINTS.search(path):
            continue
        lines = repo.lines(path)
        total_lines += len(lines)
        for number, line in enumerate(lines, start=1):
            if pattern.search(line):
                per_file[path] += 1
                samples.setdefault(path, Evidence(path=path, line=number, snippet=snippet(line)))

    total = sum(per_file.values())
    per_kloc = total / (total_lines / 1000) if total_lines else 0.0
    # Need both a real count and a real density, so one chatty script is not an epidemic.
    sev = min(severity(total, mild=5, clear=20, severe=60), severity(per_kloc, mild=2, clear=5, severe=12))
    evidence = [
        samples[path].model_copy(update={"note": f"{n} debug print(s) in this file"})
        for path, n in per_file.most_common(8)
    ]
    return Omen(
        demon="Amukku",
        sickness="log vomit",
        found=sev > 0,
        severity_hint=sev,
        summary=f"{total} debug prints ({per_kloc:.1f} per 1,000 lines) in {len(per_file)} files."
        if total
        else "No stray debug prints.",
        metrics={"total": total, "per_kloc": round(per_kloc, 2), "files": len(per_file), "lines_scanned": total_lines},
        evidence=evidence if sev else [],
    )
