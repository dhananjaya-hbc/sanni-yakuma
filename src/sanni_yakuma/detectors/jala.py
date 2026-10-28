"""Jala Sanniya (cholera, chills) -> left in the cold with no CI."""

from ..omen import Evidence, Omen
from ..repo import Repo

CI_PREFIXES = (".github/workflows/", ".circleci/", ".buildkite/", ".woodpecker/")
CI_FILES = {
    ".gitlab-ci.yml", ".travis.yml", "Jenkinsfile", "azure-pipelines.yml",
    "bitbucket-pipelines.yml", ".drone.yml", "appveyor.yml", ".appveyor.yml",
    ".woodpecker.yml", "cloudbuild.yaml",
}


def detect(repo: Repo) -> Omen:
    ci = [
        f for f in repo.files
        if f in CI_FILES
        or (f.startswith(CI_PREFIXES) and f.endswith((".yml", ".yaml")))
    ]
    found = not ci
    return Omen(
        demon="Jala", sickness="left in the cold", found=found, severity_hint=2 if found else 0,
        summary="No CI configuration; nothing checks a change before it lands." if found else f"{len(ci)} CI config file(s).",
        metrics={"ci_files": len(ci)},
        evidence=[Evidence(note="No .github/workflows, GitLab, CircleCI, Travis or Jenkins config")] if found else [],
    )
