"""Render a Ritual as one self-contained HTML page."""

import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup, escape

from .demons import BY_NAME
from .diagnosis import Ritual
from .masks import kola_svg, mask_svg
from .omen import Evidence
from .prompt import index_evidence
from .summon import parse_github

TEMPLATES = Path(__file__).parent / "templates"
TICKS = re.compile(r"`([^`]+)`")
SEVERITY = {1: "mild", 2: "clear", 3: "severe"}


def ticks(text: str) -> Markup:
    """Escape untrusted text, then show `code` spans as <code>."""
    return Markup(TICKS.sub(lambda m: f"<code>{m.group(1)}</code>", str(escape(text))))


def diff_lines(diff: str | None) -> list[tuple[str, str]]:
    if not diff:
        return []
    kinds = []
    for line in diff.splitlines():
        if line.startswith(("+++", "---")):
            kind = "file"
        elif line.startswith("@@"):
            kind = "hunk"
        elif line.startswith("+"):
            kind = "add"
        elif line.startswith("-"):
            kind = "del"
        else:
            kind = "ctx"
        kinds.append((kind, line))
    return kinds


def evidence_url(ritual: Ritual, ev: Evidence) -> str | None:
    gh = parse_github(ritual.url or "")
    if not gh or not ev.path:
        return None
    url = f"https://github.com/{gh[0]}/{gh[1]}/blob/{ritual.commit or 'HEAD'}/{quote(ev.path.rstrip('/'))}"
    return url + (f"#L{ev.line}" if ev.line else "")


def build_context(ritual: Ritual) -> dict:
    index = index_evidence(ritual.omens)
    omens = {o.demon: o for o in ritual.omens}
    demons = []
    for p in ritual.possessions:
        evidence = [(eid, index[eid][1], evidence_url(ritual, index[eid][1])) for eid in p.evidence_ids if eid in index]
        demons.append({
            "p": p,
            "info": BY_NAME[p.demon],
            "omen": omens.get(p.demon),
            "mask": Markup(mask_svg(p.demon)),
            "severity": SEVERITY[p.severity],
            "evidence": evidence,
            "diff": diff_lines(p.exorcism.diff),
        })
    spared = [{"name": name, "info": BY_NAME[name], "summary": omens[name].summary, "mask": Markup(mask_svg(name))}
              for name in ritual.spared if name in omens]
    when = datetime.fromisoformat(ritual.performed_at)
    return {
        "r": ritual,
        "demons": demons,
        "spared": spared,
        "kola_mask": Markup(kola_svg()),
        "date": when.strftime("%d %B %Y"),
        "repo_url": f"https://github.com/{'/'.join(parse_github(ritual.url))}" if ritual.url and parse_github(ritual.url) else None,
        "short_commit": (ritual.commit or "")[:7],
        "clean": [o for o in ritual.omens if not o.found],
    }


def _env() -> Environment:
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True, trim_blocks=True, lstrip_blocks=True)
    env.filters["ticks"] = ticks
    return env


def render(ritual: Ritual) -> str:
    return _env().get_template("ritual.html.j2").render(**build_context(ritual))


def page_name(ritual: Ritual) -> str:
    return ritual.repo.replace("/", "-") + ".html"


def render_gallery(rituals: list[Ritual]) -> str:
    cards = [{
        "r": r,
        "href": page_name(r),
        "masks": [Markup(mask_svg(p.demon)) for p in r.possessions],
        "date": datetime.fromisoformat(r.performed_at).strftime("%d %B %Y"),
    } for r in sorted(rituals, key=lambda r: len(r.possessions), reverse=True)]
    all_masks = [Markup(mask_svg(d)) for d in BY_NAME]
    return _env().get_template("gallery.html.j2").render(cards=cards, all_masks=all_masks)


def write_gallery(rituals: list[Ritual], folder: Path) -> Path:
    """The Hall of Masks: an index page plus every ritual page, ready for GitHub Pages."""
    folder.mkdir(parents=True, exist_ok=True)
    for ritual in rituals:
        write_page(ritual, folder / page_name(ritual))
    (folder / ".nojekyll").write_text("", encoding="utf-8")
    index = folder / "index.html"
    index.write_text(render_gallery(rituals), encoding="utf-8")
    return index


def write_page(ritual: Ritual, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(ritual), encoding="utf-8")
    return path
