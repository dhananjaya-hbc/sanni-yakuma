"""Dependency manifests, parsed just enough for Butha and Vatha."""

import json
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from ..repo import Repo

LOCKFILES = {
    "node": {"package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "bun.lock"},
    "python": {"poetry.lock", "uv.lock", "Pipfile.lock", "pdm.lock"},
    "ruby": {"Gemfile.lock"},
    "go": {"go.sum"},
    "rust": {"Cargo.lock"},
    "php": {"composer.lock"},
}

REQUIREMENTS_RE = re.compile(r"^requirements[\w.-]*\.txt$", re.IGNORECASE)
PEP508_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(\[[^\]]*\])?\s*([^;]*)")
GEM_RE = re.compile(r"""^\s*gem\s+['"]([^'"]+)['"](?:\s*,\s*['"]([^'"]+)['"])?""")


@dataclass
class Manifest:
    path: str
    ecosystem: str
    deps: dict[str, str] = field(default_factory=dict)
    dev: dict[str, str] = field(default_factory=dict)

    @property
    def folder(self) -> str:
        return str(PurePosixPath(self.path).parent)

    @property
    def total(self) -> int:
        return len(self.deps) + len(self.dev)


def _pep508(lines: list[str]) -> dict[str, str]:
    deps = {}
    for line in lines:
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith(("-", "git+", "http")):
            continue
        if match := PEP508_RE.match(line):
            deps[match.group(1).lower()] = match.group(3).strip()
    return deps


def _toml(text: str) -> dict:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return {}


def _json(text: str) -> dict:
    try:
        data = json.loads(text)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _spec(value) -> str:
    """Version spec from a TOML/JSON dependency value (string or table)."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("version", "git" if "git" in value else "path" if "path" in value else ""))
    return ""


def parse(repo: Repo, path: str) -> Manifest | None:
    name = PurePosixPath(path).name
    text = repo.read_text(path)
    if text is None:
        return None

    if name == "package.json":
        data = _json(text)
        return Manifest(path, "node", dict(data.get("dependencies") or {}), dict(data.get("devDependencies") or {}))

    if REQUIREMENTS_RE.match(name):
        deps = _pep508(text.splitlines())
        is_dev = "dev" in name.lower() or "test" in name.lower()
        return Manifest(path, "python", {} if is_dev else deps, deps if is_dev else {})

    if name == "pyproject.toml":
        data = _toml(text)
        project = data.get("project", {})
        deps = _pep508(project.get("dependencies", []))
        dev = {}
        for group in project.get("optional-dependencies", {}).values():
            dev |= _pep508(group)
        for group in data.get("dependency-groups", {}).values():
            dev |= _pep508([g for g in group if isinstance(g, str)])
        poetry = data.get("tool", {}).get("poetry", {})
        deps |= {k.lower(): _spec(v) for k, v in poetry.get("dependencies", {}).items() if k != "python"}
        dev |= {k.lower(): _spec(v) for k, v in poetry.get("dev-dependencies", {}).items()}
        for group in poetry.get("group", {}).values():
            dev |= {k.lower(): _spec(v) for k, v in group.get("dependencies", {}).items()}
        return Manifest(path, "python", deps, dev)

    if name == "Pipfile":
        data = _toml(text)
        return Manifest(
            path,
            "python",
            {k: _spec(v) for k, v in data.get("packages", {}).items()},
            {k: _spec(v) for k, v in data.get("dev-packages", {}).items()},
        )

    if name == "Cargo.toml":
        data = _toml(text)
        return Manifest(
            path,
            "rust",
            {k: _spec(v) for k, v in data.get("dependencies", {}).items()},
            {k: _spec(v) for k, v in data.get("dev-dependencies", {}).items()},
        )

    if name == "go.mod":
        deps, in_block = {}, False
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("require ("):
                in_block = True
                continue
            if in_block and line == ")":
                in_block = False
                continue
            if line.startswith("require "):
                line, in_block_line = line[len("require ") :], True
            else:
                in_block_line = in_block
            if in_block_line and line and "// indirect" not in line:
                parts = line.split()
                if len(parts) >= 2:
                    deps[parts[0]] = parts[1]
        return Manifest(path, "go", deps)

    if name == "Gemfile":
        deps = {}
        for line in text.splitlines():
            if match := GEM_RE.match(line):
                deps[match.group(1)] = match.group(2) or ""
        return Manifest(path, "ruby", deps)

    if name == "composer.json":
        data = _json(text)
        keep = lambda d: {k: v for k, v in (d or {}).items() if k != "php" and not k.startswith("ext-")}  # noqa: E731
        return Manifest(path, "php", keep(data.get("require")), keep(data.get("require-dev")))

    return None


def find_manifests(repo: Repo) -> list[Manifest]:
    found = []
    for path in repo.files:
        if repo.is_vendored(path) or "/fixtures/" in f"/{path}" or "/examples/" in f"/{path}":
            continue
        if manifest := parse(repo, path):
            found.append(manifest)
    return found


def has_lockfile(repo: Repo, manifest: Manifest) -> bool:
    """A lockfile next to the manifest or at the repo root (workspaces, monorepos)."""
    present = {p for p in repo.files if PurePosixPath(p).name in LOCKFILES.get(manifest.ecosystem, set())}
    folders = {str(PurePosixPath(p).parent) for p in present}
    return manifest.folder in folders or "." in folders
