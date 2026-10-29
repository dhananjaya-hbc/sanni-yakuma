import subprocess
from pathlib import Path

import pytest

from sanni_yakuma.repo import Repo


def _git(root: Path, *args: str, env: dict | None = None) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, env=env)


@pytest.fixture
def make_repo(tmp_path):
    """Build a throwaway git repo from {path: content} and return a Repo for it."""

    def build(files: dict[str, str | bytes], commit_date: str = "2026-10-01T12:00:00+05:30") -> Repo:
        root = tmp_path / "repo"
        root.mkdir()
        for name, content in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                path.write_bytes(content)
            else:
                path.write_text(content)
        _git(root, "init", "-q")
        _git(root, "add", "-A", "-f")
        env = {
            "GIT_AUTHOR_DATE": commit_date,
            "GIT_COMMITTER_DATE": commit_date,
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@t",
            "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
        }
        _git(root, "commit", "-q", "--allow-empty", "-m", "init", env=env)
        return Repo(root=root)

    return build
