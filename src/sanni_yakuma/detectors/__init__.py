"""Registry of demon detectors, in the order they appear in the ritual."""

from collections.abc import Callable

from ..omen import Omen
from ..repo import Repo
from . import amukku, bihiri, golu, gulma, jala, kana, kora, pith, slesma

DETECTORS: list[Callable[[Repo], Omen]] = [
    amukku.detect, bihiri.detect, golu.detect, gulma.detect, jala.detect,
    kana.detect, kora.detect, pith.detect, slesma.detect,
]


def read_omens(repo: Repo) -> list[Omen]:
    return [detect(repo) for detect in DETECTORS]
