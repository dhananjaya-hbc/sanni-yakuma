"""The diagnosis: send the omens to Gemma, check its answer, build the Ritual."""

import json
import re
import time
from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import ValidationError

from . import llm
from .demons import BY_NAME
from .diagnosis import GemmaAnswer, Possession, Ritual
from .omen import Omen
from .patch import make_diff
from .prompt import build_prompt
from .repo import Repo

TRANSIENT_RETRIES = 2
FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$")


class DiagnosisError(RuntimeError):
    pass


def extract_json(text: str) -> dict:
    """The JSON object in Gemma's reply, tolerating fences or a sentence around it."""
    text = FENCE_RE.sub("", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object in the reply")
    return json.loads(text[start : end + 1])


def ask(generate: Callable[..., str], prompt: str, model: str | None, sleep: Callable[[float], None]) -> str:
    for attempt in range(TRANSIENT_RETRIES + 1):
        try:
            return generate(prompt, model=model)
        except llm.LLMError as exc:
            if not exc.transient or attempt == TRANSIENT_RETRIES:
                raise
            sleep(15 * 3**attempt)  # 15 s, then 45 s
    raise AssertionError("unreachable")


def answer(generate: Callable[..., str], prompt: str, model: str | None,
           sleep: Callable[[float], None]) -> GemmaAnswer:
    """Ask Gemma; if the JSON is broken or the wrong shape, ask once more with the error."""
    reply = ask(generate, prompt, model, sleep)
    try:
        return GemmaAnswer.model_validate(extract_json(reply))
    except (ValueError, ValidationError) as exc:
        problem = str(exc)[:1500]
    retry = (f"{prompt}\n\n# Your previous answer could not be used\n{problem}\n"
             "Answer again with ONE valid JSON object in the exact shape above, and nothing else.")
    reply = ask(generate, retry, model, sleep)
    try:
        return GemmaAnswer.model_validate(extract_json(reply))
    except (ValueError, ValidationError) as exc:
        raise DiagnosisError(f"Gemma's answer was not valid JSON twice: {exc}") from exc


def keep_honest(ans: GemmaAnswer, omens: list[Omen], index: dict) -> tuple[list[Possession], list[str]]:
    """Drop demons no detector found and evidence ids that do not exist or belong to another demon."""
    found = {o.demon: o for o in omens if o.found}
    kept: list[Possession] = []
    rejected: list[str] = []
    for p in ans.possessions:
        name = next((n for n in BY_NAME if n.lower() == p.demon.strip().lower()), None)
        if name is None or name not in found:
            rejected.append(f"{p.demon}: no detector found this demon")
            continue
        if any(k.demon == name for k in kept):
            rejected.append(f"{name}: named twice")
            continue
        ids = [i for i in p.evidence_ids if i in index and index[i][0] == name]
        if len(ids) < len(p.evidence_ids):
            bad = sorted(set(p.evidence_ids) - set(ids))
            rejected.append(f"{name}: dropped unknown evidence {', '.join(bad)}")
        if not ids:  # the detector's own evidence is real even if Gemma cited it wrongly
            ids = [i for i, (demon, _) in index.items() if demon == name][:3]
        kept.append(p.model_copy(update={"demon": name, "evidence_ids": ids}))
    order = list(BY_NAME)
    kept.sort(key=lambda p: order.index(p.demon))
    return kept, rejected


def build_diffs(repo: Repo, possessions: list[Possession]) -> tuple[list[Possession], list[str]]:
    """Turn each find/replace patch into a real diff; drop patches whose lines are not in the code."""
    built, rejected = [], []
    for p in possessions:
        patch = p.exorcism.patch
        diff = make_diff(repo, patch) if patch else None
        if patch and diff is None:
            rejected.append(f"{p.demon}: patch for {patch.path} did not match the code, removed")
        built.append(p.model_copy(update={"exorcism": p.exorcism.model_copy(update={"diff": diff})}))
    return built, rejected


def diagnose(repo: Repo, omens: list[Omen], name: str, model: str | None = None,
             generate: Callable[..., str] = llm.generate,
             sleep: Callable[[float], None] = time.sleep) -> Ritual:
    prompt, index = build_prompt(repo, omens, name)
    ans = answer(generate, prompt, model, sleep)
    possessions, rejected = keep_honest(ans, omens, index)
    possessions, bad_diffs = build_diffs(repo, possessions)
    rejected += bad_diffs
    named = {p.demon for p in possessions}
    return Ritual(
        repo=name,
        url=repo.url,
        commit=(repo.git("rev-parse", "HEAD") or "").strip() or None,
        model=model or llm.current_model(),
        performed_at=datetime.now(UTC).isoformat(timespec="seconds"),
        omens=omens,
        blessings=ans.blessings,
        possessions=possessions,
        spared=[o.demon for o in omens if o.found and o.demon not in named],
        rejected=rejected,
        kola_sanniya=ans.kola_sanniya,
    )
