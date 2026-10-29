"""Summon: fetch the repo to examine. Accepts a GitHub URL or a local path."""

import re
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import httpx

from .repo import Repo

GITHUB_RE = re.compile(r"github\.com[/:]([^/\s]+)/([^/\s#?]+?)(?:\.git)?/?$")


def parse_github(url: str) -> tuple[str, str] | None:
    match = GITHUB_RE.search(url.strip())
    return (match.group(1), match.group(2)) if match else None


def fetch_github_meta(owner: str, name: str) -> dict:
    """Best-effort public metadata. Unauthenticated, so it may be rate-limited."""
    try:
        resp = httpx.get(
            f"https://api.github.com/repos/{owner}/{name}",
            headers={"Accept": "application/vnd.github+json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError):
        return {}
    return {
        "archived": data.get("archived"),
        "open_issues": data.get("open_issues_count"),
        "pushed_at": data.get("pushed_at"),
        "stars": data.get("stargazers_count"),
    }


@contextmanager
def summon(target: str, depth: int = 200) -> Iterator[Repo]:
    """Yield a Repo for a local folder, or shallow-clone a URL into a temp folder."""
    local = Path(target).expanduser()
    if local.is_dir():
        yield Repo(root=local.resolve())
        return

    tmp = Path(tempfile.mkdtemp(prefix="sanni-"))
    try:
        subprocess.run(
            ["git", "clone", "--quiet", "--depth", str(depth), target, str(tmp / "repo")],
            check=True,
            capture_output=True,
            text=True,
        )
        gh = parse_github(target)
        meta = fetch_github_meta(*gh) if gh else {}
        yield Repo(root=tmp / "repo", url=target, meta=meta)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
