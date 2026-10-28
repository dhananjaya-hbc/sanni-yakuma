import json

import pytest

from sanni_yakuma import llm
from sanni_yakuma.detectors import read_omens
from sanni_yakuma.exorcise import DiagnosisError, diagnose, extract_json
from sanni_yakuma.prompt import build_prompt

SICK = {
    "app.py": "def run():\n    try:\n        work()\n    except:\n        pass\n",
    "README.md": "tiny",
}


def answer(possessions, blessings=None):
    return json.dumps({
        "blessings": blessings or [{"title": "Small and focused", "detail": "One file, one job."}],
        "possessions": possessions,
        "kola_sanniya": {"root_cause": "Haste", "explanation": "Built fast.", "verse_sinhala": "සුබ වේවා",
                         "verse_transliteration": "suba vēvā", "verse_english": "May it be well"},
    }, ensure_ascii=False)


def possession(demon, ids, severity=2, patch=None):
    return {"demon": demon, "severity": severity, "evidence_ids": ids, "monologue": "I am here.",
            "exorcism": {"summary": "Fix it.", "steps": ["Do the thing."], "patch": patch}}


# Indentation is off by two on purpose: the patch step must forgive it.
GOOD_PATCH = {"path": "app.py", "find": "  except:\n      pass", "replace": "  except OSError as exc:\n      log(exc)"}
BAD_PATCH = {"path": "app.py", "find": "except ValueError:\n    pass", "replace": "x"}


class FakeGemma:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.prompts = []

    def __call__(self, prompt, model=None):
        self.prompts.append(prompt)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


@pytest.fixture
def sick(make_repo):
    repo = make_repo(SICK)
    omens = read_omens(repo)
    _, index = build_prompt(repo, omens, "demo/sick")
    bihiri_ids = [i for i, (d, _) in index.items() if d == "Bihiri"]
    return repo, omens, bihiri_ids


def test_prompt_has_evidence_ids_and_code(sick):
    repo, omens, ids = sick
    prompt, _ = build_prompt(repo, omens, "demo/sick")
    assert ids and f"- {ids[0]}: app.py:4" in prompt
    assert "    4 | " in prompt and "except:" in prompt
    assert "Never mock the ritual" in prompt


def test_extract_json_tolerates_fences():
    assert extract_json('Here you go:\n```json\n{"a": 1}\n```') == {"a": 1}


def test_diagnose_happy_path(sick):
    repo, omens, ids = sick
    gemma = FakeGemma(answer([possession("bihiri", ids)]))
    ritual = diagnose(repo, omens, "demo/sick", model="m", generate=gemma, sleep=lambda s: None)
    assert [p.demon for p in ritual.possessions] == ["Bihiri"]
    assert "Golu" in ritual.spared and ritual.rejected == []


def test_invented_demons_and_evidence_are_thrown_out(sick):
    repo, omens, ids = sick
    reply = answer([possession("Bihiri", ["E999"]), possession("Naga", ids), possession("Zombie", ids)])
    ritual = diagnose(repo, omens, "demo/sick", model="m", generate=FakeGemma(reply), sleep=lambda s: None)
    assert [p.demon for p in ritual.possessions] == ["Bihiri"]
    assert ritual.possessions[0].evidence_ids == ids  # fell back to the detector's real evidence
    assert len(ritual.rejected) == 3


def test_retries_once_on_bad_json(sick):
    repo, omens, ids = sick
    gemma = FakeGemma("not json at all", answer([possession("Bihiri", ids)]))
    ritual = diagnose(repo, omens, "demo/sick", model="m", generate=gemma, sleep=lambda s: None)
    assert len(gemma.prompts) == 2 and "could not be used" in gemma.prompts[1]
    assert ritual.possessions


def test_gives_up_after_second_bad_answer(sick):
    repo, omens, _ = sick
    with pytest.raises(DiagnosisError):
        diagnose(repo, omens, "demo/sick", model="m", generate=FakeGemma("{}", "{}"), sleep=lambda s: None)


def test_retries_server_errors(sick):
    repo, omens, ids = sick
    gemma = FakeGemma(llm.LLMError("500", transient=True), answer([possession("Bihiri", ids)]))
    assert diagnose(repo, omens, "demo/sick", model="m", generate=gemma, sleep=lambda s: None).possessions


def test_does_not_retry_auth_errors(sick):
    repo, omens, _ = sick
    with pytest.raises(llm.LLMError):
        diagnose(repo, omens, "demo/sick", model="m", generate=FakeGemma(llm.LLMError("401")), sleep=lambda s: None)


def test_patches_become_real_diffs(sick):
    repo, omens, ids = sick
    good = answer([possession("Bihiri", ids, patch=GOOD_PATCH)])
    ritual = diagnose(repo, omens, "demo/sick", model="m", generate=FakeGemma(good), sleep=lambda s: None)
    diff = ritual.possessions[0].exorcism.diff
    assert "-    except:" in diff and "+    except OSError as exc:" in diff and "+        log(exc)" in diff
    assert ritual.rejected == []

    bad = answer([possession("Bihiri", ids, patch=BAD_PATCH)])
    ritual = diagnose(repo, omens, "demo/sick", model="m", generate=FakeGemma(bad), sleep=lambda s: None)
    assert ritual.possessions[0].exorcism.diff is None and "did not match" in ritual.rejected[0]
    assert (repo.root / "app.py").read_text() == SICK["app.py"]  # never written to


def test_diff_applies_with_git(sick, tmp_path):
    import subprocess

    from sanni_yakuma.diagnosis import Patch
    from sanni_yakuma.patch import make_diff

    repo, _, _ = sick
    diff = make_diff(repo, Patch(**GOOD_PATCH))
    (tmp_path / "fix.diff").write_text(diff)
    subprocess.run(["git", "-C", str(repo.root), "apply", "--check", str(tmp_path / "fix.diff")], check=True)
