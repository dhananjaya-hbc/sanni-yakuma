"""Kora Sanniya (lameness, paralysis) -> the paralysed repo nobody moves."""

from datetime import UTC, datetime

from ..omen import Evidence, Omen
from ..repo import Repo
from .base import severity


def last_commit(repo: Repo) -> datetime | None:
    stamp = (repo.git("log", "-1", "--format=%cI") or "").strip()
    try:
        return datetime.fromisoformat(stamp) if stamp else None
    except ValueError:
        return None


def detect(repo: Repo, now: datetime | None = None) -> Omen:
    now = now or datetime.now(UTC)
    when = last_commit(repo)
    archived = bool(repo.meta.get("archived"))
    open_issues = repo.meta.get("open_issues")

    if when is None:
        return Omen(demon="Kora", sickness="paralysed repo", found=False, severity_hint=0,
                    summary="No git history to judge.", metrics={"archived": archived})

    months = (now - when).days / 30.44
    sev = severity(months, mild=6, clear=12, severe=24)
    evidence = []
    if sev:
        evidence.append(Evidence(note=f"Last commit {when.date().isoformat()}, {months:.0f} months ago"))
    if archived:
        sev = 3
        evidence.append(Evidence(note="The repository is archived on GitHub"))
    if sev and open_issues:
        evidence.append(Evidence(note=f"{open_issues} open issues and pull requests are waiting"))
    return Omen(
        demon="Kora", sickness="paralysed repo", found=sev > 0, severity_hint=sev,
        summary=f"Last commit {months:.0f} months ago" + (" (archived)." if archived else "."),
        metrics={"last_commit": when.date().isoformat(), "months_since": round(months, 1),
                 "archived": archived, "open_issues": open_issues},
        evidence=evidence,
    )
