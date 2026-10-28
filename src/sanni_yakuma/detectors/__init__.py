"""Registry of the 18 demon detectors."""

from collections.abc import Callable

from ..omen import Omen
from ..repo import Repo
from . import (abutha, amukku, bihiri, butha, deva, gedi, gini_jala, golu, gulma, jala, kana, kora, maru,
               naga, pissu, pith, slesma, vatha)

DETECTORS: list[Callable[[Repo], Omen]] = [
    amukku.detect, abutha.detect, butha.detect, bihiri.detect, deva.detect, gedi.detect,
    gini_jala.detect, golu.detect, gulma.detect, jala.detect, kana.detect, kora.detect,
    maru.detect, naga.detect, pissu.detect, pith.detect, slesma.detect, vatha.detect,
]


def read_omens(repo: Repo) -> list[Omen]:
    return [detect(repo) for detect in DETECTORS]
