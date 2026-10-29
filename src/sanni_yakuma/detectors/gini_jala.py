"""Gini Jala Sanniya (malaria, high fever) -> hotfix fever in the commit log."""

import re
from collections import Counter

from ..omen import Evidence, Omen
from ..repo import Repo
from .base import severity, snippet

FIX_RE = re.compile(r"^(fix|hotfix|bugfix)\b|\b(fix(es|ed)?|hotfix|bugfix|oops|revert|typo|broke(n)?|patch(ed)?)\b", re.IGNORECASE)
# Panic words: the fever is high when commits sound like these.
HOT_RE = re.compile(r"\b(hotfix|oops|revert|urgent|again|quick ?fix|asap|wtf|really|actually|forgot|wip)\b|!!", re.IGNORECASE)
BOT_RE = re.compile(r"\[bot\]|dependabot|renovate|github-actions", re.IGNORECASE)
# "feat: add hotfix detector" talks about fixes but is not one.
OTHER_TYPE_RE = re.compile(r"^(feat|docs|test|tests|chore|refactor|ci|build|style|perf)(\([^)]*\))?!?:", re.IGNORECASE)
MIN_COMMITS = 20


def detect(repo: Repo) -> Omen:
    log = repo.git("log", "--no-merges", "-n", "200", "--format=%cs%x1f%an%x1f%s") or ""
    commits = []
    for line in log.splitlines():
        parts = line.split("\x1f")
        if len(parts) == 3 and not BOT_RE.search(parts[1]):
            commits.append(parts)

    if len(commits) < MIN_COMMITS:
        return Omen(demon="Gini Jala", sickness="hotfix fever", found=False, severity_hint=0,
                    summary=f"Only {len(commits)} commits; too few to take the temperature.",
                    metrics={"commits": len(commits)})

    feverish = [c for c in commits if not OTHER_TYPE_RE.match(c[2])]
    fixes = [c for c in feverish if FIX_RE.search(c[2])]
    hot = [c for c in feverish if HOT_RE.search(c[2])]
    fix_days = Counter(day for day, _, _ in fixes)
    burst_day, burst = fix_days.most_common(1)[0] if fix_days else ("", 0)
    share = len(fixes) / len(commits)

    # A healthy project fixes things too; only a high share is a fever.
    sev = max(severity(share, mild=0.4, clear=0.5, severe=0.65), severity(len(hot), mild=8, clear=15, severe=30))
    evidence = [Evidence(note=f"{c[0]} · {snippet(c[2])}") for c in (hot or fixes)[:6]]
    # One busy fixing day is only a symptom when fixes are a big share overall.
    if burst >= 4 and share >= 0.25:
        sev = max(sev, 1)
        evidence.insert(0, Evidence(note=f"{burst} fix commits on {burst_day} alone"))
    return Omen(
        demon="Gini Jala", sickness="hotfix fever", found=sev > 0, severity_hint=sev,
        summary=f"{share:.0%} of the last {len(commits)} commits are fixes; {len(hot)} sound like panic.",
        metrics={"commits": len(commits), "fix_commits": len(fixes), "fix_share": round(share, 2),
                 "panic_commits": len(hot), "worst_day": burst_day or None, "worst_day_fixes": burst},
        evidence=evidence if sev else [],
    )
