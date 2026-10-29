"""Build the diagnosis prompt from the omens and a little of the repo itself."""

import json
from collections import Counter
from pathlib import PurePosixPath

from .demons import DEMONS
from .omen import Evidence, Omen
from .repo import Repo

README_CHARS = 2500
CONTEXT_BEFORE, CONTEXT_AFTER = 3, 6
MAX_SNIPPETS = 24
MAX_SNIPPET_CHARS = 14_000

STORY = """\
You are the chief performer (the edura) of a Sanni Yakuma, the traditional healing ritual of
southern Sri Lanka. In the ritual, masked dancers bring out the 18 Sanni demons one by one. Each
demon causes one illness. The performers question each demon, mock it, humble it, and send it
away. The leader of the demons, Kola Sanniya, comes last. The ritual opens with blessings.

Today the patient is a code repository. Each demon causes one code sickness. Plain detectors have
already examined the repository and collected evidence. Your job is the diagnosis and the cure."""

RULES = """\
Rules:
1. Use ONLY the evidence below. Every possession must cite evidence ids (like "E3") in
   evidence_ids. Never invent files, lines, numbers or demons. If the evidence for a suspected
   demon is weak or a false alarm, leave that demon out.
2. Severity: 1 = mild, 2 = clear, 3 = severe. The detector's hint is a starting point; judge it.
3. Respect: Sanni Yakuma is a living healing tradition. The humour is aimed only at the demons
   and the code sickness, as the ritual itself mocks the demons. Never mock the ritual, its
   performers, its beliefs, Sri Lanka, or the people who wrote the code.
4. monologue: 3 to 5 sentences of live speech in the demon's own voice, present tense, as if on
   stage: it boasts about what it did to this repo with real names and numbers from the evidence,
   the performers' mockery lands, and it gives up and leaves. Each demon has its own personality;
   never reuse the same sentence pattern for two demons, and never narrate ("I boasted that...").
   Never write evidence ids like "E12". At most one exclamation mark. Playful, never cruel.
   Never open with the demon's name or "I am" / "X is here". Example of the tone only, for a
   different, imaginary repo; do NOT reuse its words or images, invent each demon's own voice:
   "Listen to how quiet it is. Twelve times `db.py` tried to warn you, and twelve times
   `except: pass` swallowed the cry, and I fed on every one. What, you would catch `KeyError` by
   name and log it? Put those masks away. Fine, fine, I am leaving."
5. exorcism: a concrete fix for THIS repo. Name the exact functions, files and numbers from the
   evidence; generic advice such as "refactor complex functions" or "add tests" is not enough.
   summary = one sentence. steps = 1 to 6 short actions.
   patch = one small code edit, whenever the code context below is enough to write a correct
   one, otherwise null: path = the file; find = 1 to 15 consecutive lines copied exactly from
   the code context (without the "  262 | " line-number prefix); replace = the new lines.
   The find lines are searched for in the real file, so copy them character for character.
   Every demon gets a real code fix, even in an old project, because someone may fork it. Only
   for Kora (the paralysed repo): if the README says the project is deprecated, the cure is a
   clean goodbye (archive it, point users to alternatives), not reviving it.
6. blessings: up to 8 real strengths of this repo, stated in plain words with real facts from the
   overview and the absent demons (e.g. title "A README that teaches", detail "5,672 words of
   examples..."). Do not name demons in blessings and do not write "absence of" anything.
7. kola_sanniya: the single root cause behind most of the possessions, explained in 2 or 3
   sentences. Then a short blessing verse for the repo's future: 2 to 4 lines in Sinhala script
   (simple, correct Sinhala), a romanised transliteration, and an English translation.
8. Reply with ONE JSON object and nothing else. No markdown fences, no comments."""

SHAPE = """\
{
  "blessings": [{"title": "A README that teaches", "detail": "..."}],
  "possessions": [
    {
      "demon": "Bihiri",
      "severity": 2,
      "evidence_ids": ["E4", "E5"],
      "monologue": "...",
      "exorcism": {
        "summary": "...",
        "steps": ["..."],
        "patch": {
          "path": "src/app/db.py",
          "find": "    except:\n        pass",
          "replace": "    except KeyError as exc:\n        log.warning(exc)"
        }
      }
    }
  ],
  "kola_sanniya": {
    "root_cause": "...",
    "explanation": "...",
    "verse_sinhala": "...",
    "verse_transliteration": "...",
    "verse_english": "..."
  }
}"""


def demon_table() -> str:
    rows = [f"- {d.name}: causes {d.illness} -> in code: {d.sickness}" for d in DEMONS]
    return "The 18 demons:\n" + "\n".join(rows)


def index_evidence(omens: list[Omen]) -> dict[str, tuple[str, Evidence]]:
    """Give every piece of evidence of a suspected demon a stable id: E1, E2, ..."""
    index, n = {}, 0
    for omen in omens:
        if not omen.found:
            continue
        for ev in omen.evidence:
            n += 1
            index[f"E{n}"] = (omen.demon, ev)
    return index


def describe_evidence(ev: Evidence) -> str:
    where = f"{ev.path}:{ev.line}" if ev.path and ev.line else ev.path or "(repo)"
    parts = [where]
    if ev.snippet:
        parts.append(f"`{ev.snippet}`")
    if ev.note:
        parts.append(ev.note)
    return " · ".join(parts)


def omens_section(omens: list[Omen], index: dict[str, tuple[str, Evidence]]) -> str:
    ids_by_demon: dict[str, list[str]] = {}
    for eid, (demon, _) in index.items():
        ids_by_demon.setdefault(demon, []).append(eid)

    suspected, absent = [], []
    for omen in omens:
        if omen.found:
            lines = [
                f"## {omen.demon} ({omen.sickness}), detector severity hint {omen.severity_hint}",
                f"Summary: {omen.summary}",
                f"Metrics: {json.dumps(omen.metrics, ensure_ascii=False)}",
            ]
            lines += [f"- {eid}: {describe_evidence(index[eid][1])}" for eid in ids_by_demon.get(omen.demon, [])]
            suspected.append("\n".join(lines))
        else:
            absent.append(f"- {omen.demon} ({omen.sickness}): {omen.summary}")
    return (
        "# Suspected demons (with evidence)\n\n"
        + "\n\n".join(suspected or ["(none)"])
        + "\n\n# Absent demons (possible blessings)\n"
        + "\n".join(absent or ["(none)"])
    )


def code_context(repo: Repo, index: dict[str, tuple[str, Evidence]]) -> str:
    """Numbered source lines around the evidence, so the exorcism can be a real diff."""
    blocks, used, seen = [], 0, set()
    for eid, (_, ev) in index.items():
        if len(blocks) >= MAX_SNIPPETS or not (ev.path and ev.line) or (ev.path, ev.line // 10) in seen:
            continue
        lines = repo.lines(ev.path)
        if not lines:
            continue
        start = max(1, ev.line - CONTEXT_BEFORE)
        end = min(len(lines), ev.line + CONTEXT_AFTER)
        body = "\n".join(f"{n:>5} | {lines[n - 1][:200]}" for n in range(start, end + 1))
        block = f"--- {ev.path} (lines {start}-{end}, for {eid})\n{body}"
        if used + len(block) > MAX_SNIPPET_CHARS:
            break
        blocks.append(block)
        used += len(block)
        seen.add((ev.path, ev.line // 10))
    return "# Code around the evidence\n\n" + ("\n\n".join(blocks) if blocks else "(none)")


def repo_overview(repo: Repo, name: str) -> str:
    top = sorted({PurePosixPath(f).parts[0] + ("/" if "/" in f else "") for f in repo.files})
    langs = Counter(PurePosixPath(f).suffix for f in repo.source_files).most_common(6)
    readme = next((f for f in repo.files if "/" not in f and f.lower().startswith("readme")), None)
    text = (repo.read_text(readme) or "")[:README_CHARS] if readme else "(no README)"
    return (
        f"# The patient: {name}\n"
        f"Files: {len(repo.files)} tracked, {len(repo.source_files)} source, {len(repo.test_files)} test.\n"
        f"Languages: {', '.join(f'{ext} x{n}' for ext, n in langs) or 'none'}\n"
        f"Top level: {', '.join(top[:40])}\n\n"
        f"README (start):\n<<<\n{text}\n>>>"
    )


def build_prompt(repo: Repo, omens: list[Omen], name: str) -> tuple[str, dict[str, tuple[str, Evidence]]]:
    index = index_evidence(omens)
    prompt = "\n\n".join(
        [
            STORY,
            demon_table(),
            RULES,
            repo_overview(repo, name),
            omens_section(omens, index),
            code_context(repo, index),
            "# Answer with JSON in exactly this shape\n" + SHAPE,
        ]
    )
    return prompt, index
