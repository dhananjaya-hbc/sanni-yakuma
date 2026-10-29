"""Naga Sanniya (snake nightmares) -> security nightmares: secrets in the code.

Every secret is masked before it becomes evidence, so the ritual page
never spreads the poison further.
"""

import math
import re
from collections import Counter
from pathlib import PurePosixPath

from ..omen import Evidence, Omen
from ..repo import Repo, is_test_path
from .base import MAX_EVIDENCE, snippet

KNOWN_KEYS = {
    "AWS access key": re.compile(r"\b((?:AKIA|ASIA)[0-9A-Z]{16})\b"),
    "GitHub token": re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b"),
    "Google API key": re.compile(r"\b(AIza[0-9A-Za-z_\-]{35})\b"),
    "Slack token": re.compile(r"\b(xox[baprs]-[A-Za-z0-9-]{10,})\b"),
    "Stripe live key": re.compile(r"\b((?:sk|rk)_live_[0-9a-zA-Z]{20,})\b"),
    "AI API key": re.compile(r"\b(sk-(?:proj-|ant-)?[A-Za-z0-9_\-]{32,})\b"),
    "private key": re.compile(r"(-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY-----)"),
}
GENERIC = re.compile(
    r"""(?i)\b\w*(password|passwd|pwd|secret|api_?key|access_?key|auth_?token|token)\w*["']?\s*[:=]\s*["']([^"'\s]{8,})["']"""
)
PLACEHOLDER = re.compile(
    r"(?i)your|my[-_]|xxx|example|changeme|placeholder|dummy|sample|test|fake|<|\$\{|\{\{|%s|\*\*\*|process\.env|environ"
)
ENV_FILE = re.compile(r"^\.env(\.[\w-]+)?$")
SAFE_ENV = re.compile(r"\.(example|sample|template|dist|defaults?)$")
DOC_EXTS = (".md", ".rst", ".txt", ".adoc", ".html", ".ipynb")
DOC_DIRS = {"docs", "doc", "examples", "example", "samples", "fixtures"}
SKIP_NAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
    "Cargo.lock",
    "go.sum",
    "composer.lock",
}


def mask(secret: str) -> str:
    if secret.startswith("-----"):
        return "-----BEGIN ****PRIVATE KEY-----"
    keep = 4 if len(secret) >= 12 else 2
    return secret[:keep] + "*" * 8 + secret[-2:]


def entropy(text: str) -> float:
    counts = Counter(text)
    return -sum(n / len(text) * math.log2(n / len(text)) for n in counts.values())


def detect(repo: Repo) -> Omen:
    evidence: list[Evidence] = []
    kinds: Counter[str] = Counter()

    for path in repo.files:
        name = PurePosixPath(path).name
        if ENV_FILE.match(name) and not SAFE_ENV.search(name):
            kinds["committed .env"] += 1
            evidence.append(Evidence(path=path, note="environment file with real settings is committed"))

    for path in repo.files:
        name = PurePosixPath(path).name
        # Test fixtures hold throwaway certificates and fake keys on purpose.
        if repo.is_vendored(path) or name in SKIP_NAMES or is_test_path(path):
            continue
        docs = path.lower().endswith(DOC_EXTS) or bool(DOC_DIRS & set(PurePosixPath(path).parts[:-1]))
        for number, line in enumerate(repo.lines(path), start=1):
            if len(line) > 2000:  # minified or data blobs
                continue
            for kind, pattern in KNOWN_KEYS.items():
                for match in pattern.finditer(line):
                    if "EXAMPLE" in match.group(1):  # AWS's documented sample key
                        continue
                    kinds[kind] += 1
                    evidence.append(
                        Evidence(
                            path=path,
                            line=number,
                            note=kind,
                            snippet=snippet(line.replace(match.group(1), mask(match.group(1)))),
                        )
                    )
            if docs:
                continue
            for match in GENERIC.finditer(line):
                value = match.group(2)
                if PLACEHOLDER.search(value) or entropy(value) < 3.0:
                    continue
                kinds["hard-coded " + match.group(1).lower()] += 1
                evidence.append(
                    Evidence(
                        path=path,
                        line=number,
                        note="hard-coded credential",
                        snippet=snippet(line.replace(value, mask(value))),
                    )
                )

    real = sum(n for k, n in kinds.items() if not k.startswith("hard-coded"))
    generic = sum(n for k, n in kinds.items() if k.startswith("hard-coded"))
    if real:
        sev = 3
    elif generic >= 3:
        sev = 2
    elif generic:
        sev = 1
    else:
        sev = 0
    # Known key formats first: they are the real venom.
    evidence.sort(key=lambda e: e.note == "hard-coded credential")
    return Omen(
        demon="Naga",
        sickness="security nightmares",
        found=sev > 0,
        severity_hint=sev,
        summary=("Secrets in the code: " + ", ".join(f"{n} {k}" for k, n in kinds.most_common()) + ". (Masked here.)")
        if sev
        else "No secrets found.",
        metrics={"known_secrets": real, "suspected_secrets": generic},
        evidence=evidence[:MAX_EVIDENCE],
    )
