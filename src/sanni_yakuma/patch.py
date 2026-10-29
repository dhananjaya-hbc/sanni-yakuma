"""Turn Gemma's find/replace edit into a real unified diff, or nothing.

Models are bad at writing unified diffs by hand (line numbers, hunk headers,
whitespace). So Gemma only says which lines to find and what to put instead;
we locate them in the real file and let difflib write the diff.
"""

import ast
import difflib

from .diagnosis import Patch
from .repo import Repo


def indent_of(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def locate(lines: list[str], find: list[str]) -> int | None:
    """Index where `find` occurs exactly once, ignoring indentation; None if absent or ambiguous."""
    wanted = [line.strip() for line in find]
    hits = [i for i in range(len(lines) - len(find) + 1)
            if [line.strip() for line in lines[i : i + len(find)]] == wanted]
    return hits[0] if len(hits) == 1 else None


def reindent(replace: list[str], given_first: str, actual_first: str) -> list[str]:
    """Shift the replacement by however much Gemma got the indentation wrong."""
    given, actual = indent_of(given_first), indent_of(actual_first)
    if given == actual:
        return replace
    out = []
    for line in replace:
        if not line.strip():
            out.append(line)
        elif line.startswith(given):
            out.append(actual + line[len(given):])
        else:
            out.append(actual + line.lstrip())
    return out


def still_valid(path: str, text: str) -> bool:
    """A cure must not break the patient: patched Python has to parse."""
    if not path.endswith(".py"):
        return True
    try:
        ast.parse(text)
    except SyntaxError:
        return False
    return True


def make_diff(repo: Repo, patch: Patch) -> str | None:
    text = repo.read_text(patch.path)
    if text is None or patch.path not in repo.files:
        return None
    lines = text.splitlines()
    find = [line for line in patch.find.splitlines()]
    while find and not find[0].strip():
        find.pop(0)
    while find and not find[-1].strip():
        find.pop()
    if not find:
        return None
    start = locate(lines, find)
    if start is None:
        return None
    replace = reindent(patch.replace.splitlines(), find[0], lines[start])
    new = lines[:start] + replace + lines[start + len(find):]
    if new == lines or not still_valid(patch.path, "\n".join(new)):
        return None
    diff = difflib.unified_diff(lines, new, f"a/{patch.path}", f"b/{patch.path}", n=2, lineterm="")
    return "\n".join(diff) + "\n"
