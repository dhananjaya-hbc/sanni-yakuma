"""Command line: `sanni omens`, `sanni exorcise`, `sanni render` and `sanni ping`."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from . import __version__
from .detectors import read_omens
from .diagnosis import Ritual
from .exorcise import DiagnosisError, diagnose
from .llm import LLMError, generate
from .render import write_page
from .summon import parse_github, summon

console = Console()
SEVERITY = {0: "[dim]absent[/]", 1: "[yellow]mild[/]", 2: "[orange1]clear[/]", 3: "[bold red]severe[/]"}


def cmd_omens(args: argparse.Namespace) -> int:
    try:
        with console.status(f"Summoning {args.target} ..."), summon(args.target) as repo:
            omens = read_omens(repo)
    except subprocess.CalledProcessError as exc:
        console.print(f"[red]Could not clone {args.target}:[/] {exc.stderr.strip()}")
        return 1

    if args.json:
        print(json.dumps([o.model_dump(exclude_none=True) for o in omens], indent=2))
        return 0

    table = Table(title=f"Omens for {args.target}", show_lines=True)
    table.add_column("Demon", style="bold")
    table.add_column("Sickness")
    table.add_column("Severity")
    table.add_column("Omen")
    for omen in sorted(omens, key=lambda o: -o.severity_hint):
        table.add_row(omen.demon, omen.sickness, SEVERITY[omen.severity_hint], omen.summary)
    console.print(table)

    for omen in omens:
        if not omen.found or not omen.evidence:
            continue
        console.print(f"\n[bold]{omen.demon}[/] evidence:")
        for ev in omen.evidence[: args.limit]:
            where = f"{ev.path}:{ev.line}" if ev.path and ev.line else ev.path or ""
            text = " · ".join(x for x in (where, ev.snippet, ev.note) if x)
            console.print(f"  • {text}", markup=False, highlight=False)
    found = sum(o.found for o in omens)
    console.print(f"\n[bold]{found}[/] of {len(omens)} demons possess this repo.")
    return 0


def repo_name(target: str) -> str:
    if gh := parse_github(target):
        return f"{gh[0]}/{gh[1]}"
    return Path(target).expanduser().resolve().name


def cmd_exorcise(args: argparse.Namespace) -> int:
    name = repo_name(args.target)
    try:
        with summon(args.target) as repo:
            with console.status(f"Reading the omens of {name} ..."):
                omens = read_omens(repo)
            with console.status(f"Gemma is diagnosing {name} ..."):
                ritual = diagnose(repo, omens, name, model=args.model)
    except subprocess.CalledProcessError as exc:
        console.print(f"[red]Could not clone {args.target}:[/] {exc.stderr.strip()}")
        return 1
    except (LLMError, DiagnosisError) as exc:
        console.print(f"[red]{exc}[/]")
        return 1

    out = Path(args.out) / f"{name.replace('/', '-')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(ritual.model_dump_json(indent=2), encoding="utf-8")

    console.print(f"\n[bold]Ata Paliya[/]: {len(ritual.blessings)} blessings")
    for b in ritual.blessings:
        console.print(f"  ✦ {b.title}", highlight=False)
    console.print(f"\n[bold]Daha Ata Sanniya[/]: {len(ritual.possessions)} demons possess {name}")
    for p in ritual.possessions:
        console.print(f"\n  {p.demon} {SEVERITY[p.severity]}", highlight=False)
        console.print(f"  [italic]{p.monologue}[/]", highlight=False)
        console.print(f"  Exorcism: {p.exorcism.summary}", highlight=False)
        if p.exorcism.diff:
            console.print(p.exorcism.diff, markup=False, highlight=False)
    if ritual.spared:
        console.print(f"\n[dim]Spared after questioning: {', '.join(ritual.spared)}[/]")
    if ritual.rejected:
        console.print(f"[dim]Thrown out: {'; '.join(ritual.rejected)}[/]")
    k = ritual.kola_sanniya
    console.print(f"\n[bold]Kola Sanniya[/]: {k.root_cause}", highlight=False)
    console.print(k.explanation, highlight=False)
    console.print(f"\n{k.verse_sinhala}\n[dim]{k.verse_transliteration}[/]\n[italic]{k.verse_english}[/]", highlight=False)
    page = write_page(ritual, out.with_suffix(".html"))
    console.print(f"\nSaved {out} and {page}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    """Re-render pages from saved rituals, without asking Gemma again."""
    for name in args.rituals:
        source = Path(name)
        ritual = Ritual.model_validate_json(source.read_text(encoding="utf-8"))
        page = write_page(ritual, source.with_suffix(".html"))
        console.print(f"Rendered {page}")
    return 0


def cmd_ping(args: argparse.Namespace) -> int:
    try:
        reply = generate("Reply with exactly one short sentence: are you awake?", model=args.model)
    except LLMError as exc:
        console.print(f"[red]{exc}[/]")
        return 1
    console.print(reply.strip())
    return 0


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(prog="sanni", description="An AI exorcism for codebases.")
    parser.add_argument("--version", action="version", version=f"sanni {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    omens = sub.add_parser("omens", help="read the omens: run the detectors, no AI")
    omens.add_argument("target", help="GitHub URL or local folder")
    omens.add_argument("--json", action="store_true", help="print raw JSON")
    omens.add_argument("--limit", type=int, default=5, help="evidence lines per demon")
    omens.set_defaults(func=cmd_omens)

    exorcise = sub.add_parser("exorcise", help="perform the ritual: omens, then Gemma's diagnosis and cure")
    exorcise.add_argument("target", help="GitHub URL or local folder")
    exorcise.add_argument("--model", help="override MODEL_NAME, e.g. gemma-4-31b-it")
    exorcise.add_argument("--out", default="out", help="folder for the ritual JSON and page (default: out)")
    exorcise.set_defaults(func=cmd_exorcise)

    render = sub.add_parser("render", help="re-render ritual pages from saved JSON (no AI)")
    render.add_argument("rituals", nargs="+", help="out/<repo>.json files")
    render.set_defaults(func=cmd_render)

    ping = sub.add_parser("ping", help="check that Gemma answers")
    ping.add_argument("--model", help="override MODEL_NAME")
    ping.set_defaults(func=cmd_ping)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
