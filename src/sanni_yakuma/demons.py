"""The 18 Sanni demons: traditional illness and the code sickness each one causes here.

Illnesses follow the Wikipedia article "Sanni Yakuma" (to be checked against a
second source before publishing).
"""

from typing import NamedTuple


class Demon(NamedTuple):
    name: str
    illness: str
    sickness: str


DEMONS = [
    Demon("Amukku", "vomiting and stomach disease", "log vomit"),
    Demon("Abutha", "madness not caused by spirits", "self-made complexity"),
    Demon("Butha", "madness caused by spirits", "dependency hell"),
    Demon("Bihiri", "deafness", "swallowed errors"),
    Demon("Deva", "epidemics", "copy-paste spreading"),
    Demon("Gedi", "boils and skin disease", "style sores"),
    Demon("Gini Jala", "malaria and high fever", "hotfix fever"),
    Demon("Golu", "muteness", "silent repo"),
    Demon("Gulma", "worms and stomach parasites", "hidden worms"),
    Demon("Jala", "cholera and chills", "left in the cold"),
    Demon("Kana", "blindness", "can't see if it works"),
    Demon("Kora", "lameness and paralysis", "paralysed repo"),
    Demon("Maru", "delirium and death", "dead code"),
    Demon("Naga", "snake nightmares", "security nightmares"),
    Demon("Pissu", "temporary madness", "magic madness"),
    Demon("Pith", "bile", "bitter legal trouble"),
    Demon("Slesma", "phlegm and epilepsy", "clogged repo"),
    Demon("Vatha", "bloating and rheumatism", "dependency bloat"),
]

BY_NAME = {d.name: d for d in DEMONS}
