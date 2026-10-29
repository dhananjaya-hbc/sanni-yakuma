"""The ritual as a Markdown pull-request comment."""

from .demons import BY_NAME
from .diagnosis import Ritual
from .prompt import index_evidence
from .render import SEVERITY, evidence_url

MARKER = "<!-- sanni-yakuma -->"
MAX_EVIDENCE = 5


def quiet(text: str) -> str:
    """Stop Gemma's text from pinging people or closing issues from a comment."""
    return text.replace("@", "@​").replace("#", "#​")


def comment(ritual: Ritual) -> str:
    index = index_evidence(ritual.omens)
    found = len(ritual.possessions)
    short = (ritual.commit or "")[:7]
    out = [
        MARKER,
        f"## Sanni Yakuma · {found} of 18 demons possess this code",
        f"_Diagnosed by {ritual.model}" + (f" at `{short}`" if short else "") + "._",
        "",
    ]
    if ritual.blessings:
        out.append("**Ata Paliya, the blessings:** " + " · ".join(quiet(b.title) for b in ritual.blessings))
        out.append("")

    for p in ritual.possessions:
        info = BY_NAME[p.demon]
        out += [f"### {p.demon} Sanniya · {info.sickness} ({SEVERITY[p.severity]})", ""]
        out += ["> " + quiet(p.monologue).replace("\n", "\n> "), ""]
        out.append(f"**Exorcism:** {quiet(p.exorcism.summary)}")
        out += [f"{i}. {quiet(step)}" for i, step in enumerate(p.exorcism.steps, start=1)]
        evidence = []
        for eid in p.evidence_ids[:MAX_EVIDENCE]:
            if eid not in index:
                continue
            ev = index[eid][1]
            where = f"{ev.path}:{ev.line}" if ev.path and ev.line else ev.path or ""
            url = evidence_url(ritual, ev)
            label = f"[`{where}`]({url})" if url and where else (f"`{where}`" if where else "")
            evidence.append("- " + " ".join(x for x in (label, quiet(ev.note or "")) if x))
        if evidence or p.exorcism.diff:
            out += ["", "<details><summary>Evidence and fix</summary>", ""]
            out += evidence
            if p.exorcism.diff:
                out += ["", "~~~~diff", p.exorcism.diff.rstrip("\n").replace("~~~~", "~ ~ ~ ~"), "~~~~"]
            out += ["", "</details>"]
        out.append("")

    if not ritual.possessions:
        out += ["No demon could be proven. The patient is well.", ""]
    if ritual.spared:
        out += [f"_Questioned and sent away: {', '.join(ritual.spared)}._", ""]

    k = ritual.kola_sanniya
    out += [
        "### Kola Sanniya, the root cause",
        quiet(k.root_cause),
        "",
        f"> {quiet(k.verse_sinhala)}  ",
        f"> _{quiet(k.verse_transliteration)}_  ",
        f"> {quiet(k.verse_english)}",
        "",
        "<sub>Every demon here rests on evidence the detectors found in the code; anything Gemma claimed "
        "beyond that was thrown out. The full ritual page is in this run's `sanni-yakuma` artifact. "
        "Made with [sanni-yakuma](https://github.com/dhananjaya-hbc/sanni-yakuma).</sub>",
    ]
    return "\n".join(out) + "\n"
