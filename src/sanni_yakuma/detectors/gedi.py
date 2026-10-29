"""Gedi Sanniya (boils, skin disease) -> style sores: no linter or formatter."""

import json
import tomllib
from pathlib import PurePosixPath

from ..omen import Evidence, Omen
from ..repo import Repo

LINT_FILES = {
    ".eslintrc",
    ".eslintrc.js",
    ".eslintrc.cjs",
    ".eslintrc.json",
    ".eslintrc.yml",
    ".eslintrc.yaml",
    "eslint.config.js",
    "eslint.config.mjs",
    "eslint.config.cjs",
    "eslint.config.ts",
    ".prettierrc",
    ".prettierrc.json",
    ".prettierrc.js",
    ".prettierrc.yml",
    ".prettierrc.yaml",
    "prettier.config.js",
    "prettier.config.mjs",
    "biome.json",
    "biome.jsonc",
    "deno.json",
    ".flake8",
    ".pylintrc",
    "pylintrc",
    "ruff.toml",
    ".ruff.toml",
    "tox.ini",
    ".isort.cfg",
    ".rubocop.yml",
    ".golangci.yml",
    ".golangci.yaml",
    "rustfmt.toml",
    ".rustfmt.toml",
    "clippy.toml",
    ".clang-format",
    ".clang-tidy",
    "checkstyle.xml",
    ".scalafmt.conf",
    "phpcs.xml",
    ".php-cs-fixer.php",
    ".pre-commit-config.yaml",
    ".stylelintrc",
    ".stylelintrc.json",
    "analysis_options.yaml",
    ".swiftlint.yml",
}
# Zero-config linters that only show up as a dev dependency.
LINT_PACKAGES = {"standard", "xo", "eslint", "prettier", "@biomejs/biome", "semistandard", "ts-standard"}
PYPROJECT_TOOLS = {"ruff", "black", "isort", "pylint", "flake8", "autopep8", "yapf"}


def _tool_table(text: str) -> dict:
    try:
        return tomllib.loads(text).get("tool", {})
    except tomllib.TOMLDecodeError:
        return {}


def _json(text: str) -> dict:
    try:
        data = json.loads(text)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def configured_in_metadata(repo: Repo) -> list[str]:
    found = []
    if text := repo.read_text("pyproject.toml"):
        found += [f"pyproject.toml [tool.{t}]" for t in sorted(PYPROJECT_TOOLS & _tool_table(text).keys())]
    if text := repo.read_text("setup.cfg"):
        found += [f"setup.cfg [{t}]" for t in ("flake8", "pylint", "isort") if f"[{t}" in text]
    if text := repo.read_text("package.json"):
        data = _json(text)
        found += [f"package.json {k}" for k in ("eslintConfig", "prettier") if k in data]
        dev = data.get("devDependencies") or {}
        found += [f"package.json devDependency {p}" for p in sorted(LINT_PACKAGES & set(dev))]
    return found


def detect(repo: Repo) -> Omen:
    if not repo.source_files:
        return Omen(
            demon="Gedi", sickness="style sores", found=False, severity_hint=0, summary="No source code to style."
        )
    configs = [f for f in repo.files if PurePosixPath(f).name in LINT_FILES and not repo.is_vendored(f)]
    configs += configured_in_metadata(repo)
    gofmt = any(f.endswith(".go") for f in repo.source_files)  # Go has one true format built in
    editorconfig = repo.exists(".editorconfig")

    if configs or gofmt:
        sev, summary, evidence = 0, f"Style is kept: {', '.join(configs[:3]) or 'gofmt'}.", []
    elif editorconfig:
        sev, summary = 1, "Only .editorconfig; no linter or formatter."
        evidence = [Evidence(path=".editorconfig", note="sets whitespace only; nothing checks the code itself")]
    else:
        sev, summary = 2, "No linter, formatter or .editorconfig; every file follows its own style."
        evidence = [
            Evidence(note="No ESLint, Prettier, Ruff, Black, Flake8, RuboCop, golangci, rustfmt or pre-commit config")
        ]
    return Omen(
        demon="Gedi",
        sickness="style sores",
        found=sev > 0,
        severity_hint=sev,
        summary=summary,
        metrics={"style_configs": len(configs), "editorconfig": editorconfig},
        evidence=evidence,
    )
