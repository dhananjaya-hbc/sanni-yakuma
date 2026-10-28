"""Command line: `sanni omens <repo>` and `sanni ping`."""

import argparse
import json
import subprocess
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from . import __version__
from .detectors import read_omens
from .llm import LLMError, generate
from .summon import summon

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

    ping = sub.add_parser("ping", help="check that Gemma answers")
    ping.add_argument("--model", help="override MODEL_NAME")
    ping.set_defaults(func=cmd_ping)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
