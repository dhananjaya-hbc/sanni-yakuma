"""Pith Sanniya (bile) -> bitter legal trouble: no LICENSE."""

import json
import re
import tomllib

from ..omen import Evidence, Omen
from ..repo import Repo

LICENSE_RE = re.compile(r"^(license|licence|copying|unlicense)([.-].*)?$", re.IGNORECASE)


def _load(repo: Repo, path: str) -> dict:
    """Parsed package metadata, or {} if missing or malformed."""
    text = repo.read_text(path)
    if text is None:
        return {}
    try:
        data = json.loads(text) if path.endswith(".json") else tomllib.loads(text)
    except (ValueError, tomllib.TOMLDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def declared_license(repo: Repo) -> str | None:
    """License named in package metadata, if any."""
    candidates = [
        _load(repo, "package.json").get("license"),
        _load(repo, "pyproject.toml").get("project", {}).get("license"),
        _load(repo, "Cargo.toml").get("package", {}).get("license"),
    ]
    for value in candidates:
        if isinstance(value, dict):  # pyproject: license = {text = "MIT"}
            value = value.get("text") or value.get("file")
        if isinstance(value, str) and value:
            return value
    return None


def detect(repo: Repo) -> Omen:
    files = [f for f in repo.files if "/" not in f and LICENSE_RE.match(f)]
    declared = declared_license(repo)
    if files:
        sev, summary, evidence = 0, f"License file: {files[0]}.", []
    elif declared:
        sev = 1
        summary = f"License '{declared}' is declared in package metadata, but there is no LICENSE file."
        evidence = [Evidence(note=summary)]
    else:
        sev = 3
        summary = "No license at all: by default, nobody may legally reuse this code."
        evidence = [Evidence(note="No LICENSE/COPYING file and no license field in package metadata")]
    return Omen(
        demon="Pith", sickness="bitter legal trouble", found=sev > 0, severity_hint=sev,
        summary=summary,
        metrics={"license_file": files[0] if files else None, "declared_license": declared},
        evidence=evidence,
    )
