"""Original SVG masks for the 18 Sanni demons and Kola Sanniya.

Drawn from code in one shared style (bulging eyes, fangs, a crown, lacquer
colours) so no photo of a real mask is copied. Each demon gets one trait that
hints at the illness it causes.
"""

from dataclasses import dataclass, field

RED, YELLOW, GREEN, BLACK, CREAM = "#b3261e", "#e0a526", "#3f7d3a", "#1d1a17", "#f2e8d5"
BLUE, PALE, ORANGE, BILE = "#3b5f8a", "#d9cfb8", "#e2711d", "#8a9a2b"


@dataclass(frozen=True)
class Look:
    face: str
    crown: str = YELLOW
    eyes: str = "round"  # round | blank | spiral | sleepy | rolling | hollow
    mouth: str = "fangs"  # fangs | open | sealed | chatter | tusks
    crown_kind: str = "flames"  # flames | cobras | fire | wisps | copies | none
    marks: tuple[str, ...] = field(default_factory=tuple)  # boils, worms, drip, cheeks, swirl, bound, spots


LOOKS = {
    "Amukku": Look(face=GREEN, crown=YELLOW, mouth="open"),
    "Abutha": Look(face=ORANGE, crown=RED, eyes="rolling", marks=("swirl",)),
    "Butha": Look(face=BLUE, crown=PALE, crown_kind="wisps", eyes="rolling"),
    "Bihiri": Look(face=YELLOW, crown=RED, marks=("bound",)),
    "Deva": Look(face=RED, crown=YELLOW, crown_kind="copies", marks=("spots",)),
    "Gedi": Look(face=YELLOW, crown=GREEN, marks=("boils",)),
    "Gini Jala": Look(face=RED, crown=ORANGE, crown_kind="fire", marks=("sweat",)),
    "Golu": Look(face=PALE, crown=RED, mouth="sealed"),
    "Gulma": Look(face=GREEN, crown=RED, marks=("worms",)),
    "Jala": Look(face=BLUE, crown=CREAM, mouth="chatter", eyes="sleepy"),
    "Kana": Look(face=BLACK, crown=YELLOW, eyes="blank"),
    "Kora": Look(face=ORANGE, crown=GREEN, eyes="sleepy", marks=("droop",)),
    "Maru": Look(face=PALE, crown=BLACK, eyes="hollow", mouth="tusks"),
    "Naga": Look(face=GREEN, crown=BLACK, crown_kind="cobras"),
    "Pissu": Look(face=YELLOW, crown=BLUE, eyes="spiral"),
    "Pith": Look(face=BILE, crown=YELLOW, mouth="open", marks=("drip",)),
    "Slesma": Look(face=BLUE, crown=GREEN, marks=("drip", "cheeks")),
    "Vatha": Look(face=ORANGE, crown=YELLOW, marks=("cheeks",), mouth="tusks"),
}


def _crown(look: Look) -> str:
    kind, c = look.crown_kind, look.crown
    if kind == "none":
        return ""
    if kind == "cobras":
        hoods = []
        for x in (52, 76, 100, 124, 148):
            top = 14 if x == 100 else 24
            hoods.append(
                f'<path d="M{x},74 C{x - 17},62 {x - 15},{top + 6} {x},{top} C{x + 15},{top + 6} {x + 17},62 {x},74 Z" '
                f'fill="{GREEN}" stroke="{BLACK}" stroke-width="3"/>'
                f'<path d="M{x - 5},{top + 22} Q{x},{top + 30} {x + 5},{top + 22}" stroke="{YELLOW}" stroke-width="3" fill="none"/>'
                f'<circle cx="{x - 5}" cy="{top + 13}" r="2.5" fill="{RED}"/><circle cx="{x + 5}" cy="{top + 13}" r="2.5" fill="{RED}"/>'
            )
        return "".join(hoods)
    if kind == "wisps":
        return "".join(
            f'<path d="M{x},72 C{x - 14},52 {x + 14},40 {x},22 C{x - 10},38 {x + 12},52 {x},72" fill="none" '
            f'stroke="{c}" stroke-width="5" stroke-linecap="round" opacity="0.85"/>'
            for x in (50, 75, 100, 125, 150)
        )
    if kind == "copies":
        out = []
        for x in (46, 73, 100, 127, 154):
            out.append(
                f'<circle cx="{x}" cy="40" r="13" fill="{c}" stroke="{BLACK}" stroke-width="3"/>'
                f'<circle cx="{x - 4}" cy="38" r="2.6" fill="{BLACK}"/><circle cx="{x + 4}" cy="38" r="2.6" fill="{BLACK}"/>'
                f'<path d="M{x - 5},45 Q{x},49 {x + 5},45" stroke="{BLACK}" stroke-width="2" fill="none"/>'
            )
        return "".join(out)
    tall = kind == "fire"
    flames = []
    for i, x in enumerate(range(40, 161, 20)):
        top = (6 if tall else 22) + abs(3 - i) * (8 if tall else 5)
        fill = (RED, ORANGE, YELLOW)[i % 3] if tall else c
        flames.append(
            f'<path d="M{x - 12},76 Q{x - 15},{top + 26} {x},{top} Q{x + 15},{top + 26} {x + 12},76 Z" '
            f'fill="{fill}" stroke="{BLACK}" stroke-width="3" stroke-linejoin="round"/>'
        )
    return "".join(flames)


def _ears(look: Look) -> str:
    ink = CREAM if look.face == BLACK else BLACK
    ears = (f'<ellipse cx="38" cy="128" rx="13" ry="23" fill="{look.face}" stroke="{ink}" stroke-width="4"/>'
            f'<ellipse cx="162" cy="128" rx="13" ry="23" fill="{look.face}" stroke="{ink}" stroke-width="4"/>')
    if "bound" in look.marks:  # Bihiri: deafness, ears tied shut
        for x in (38, 162):
            ears += "".join(
                f'<line x1="{x - 15}" y1="{y}" x2="{x + 15}" y2="{y + 6}" stroke="{CREAM}" stroke-width="5"/>'
                for y in (114, 124, 134)
            )
    return ears


def _eye(cx: int, cy: int, look: Look) -> str:
    rim = f'<circle cx="{cx}" cy="{cy}" r="18" fill="{CREAM}" stroke="{RED if look.face != RED else BLACK}" stroke-width="5"/>'
    kind = look.eyes
    if kind == "blank":  # Kana: blindness
        return rim + f'<path d="M{cx - 9},{cy - 9} L{cx + 9},{cy + 9} M{cx + 9},{cy - 9} L{cx - 9},{cy + 9}" stroke="{PALE}" stroke-width="3"/>'
    if kind == "hollow":  # Maru: death
        return f'<circle cx="{cx}" cy="{cy}" r="18" fill="{BLACK}" stroke="{BLACK}" stroke-width="5"/><circle cx="{cx}" cy="{cy}" r="3" fill="{RED}"/>'
    if kind == "spiral":  # Pissu: madness
        return rim + (f'<path d="M{cx},{cy} m-2,0 a2,2 0 1,1 4,0 a5,5 0 1,1 -9,0 a8,8 0 1,1 15,0 a11,11 0 1,1 -21,0" '
                      f'fill="none" stroke="{BLACK}" stroke-width="2.5"/>')
    pupil_y = cy - 8 if kind == "rolling" else cy
    eye = rim + f'<circle cx="{cx}" cy="{pupil_y}" r="7.5" fill="{BLACK}"/><circle cx="{cx - 2}" cy="{pupil_y - 2}" r="2" fill="{CREAM}"/>'
    if kind == "sleepy":  # Kora, Jala: heavy lids
        eye += f'<path d="M{cx - 20},{cy - 1} Q{cx},{cy - 26} {cx + 20},{cy - 1} Z" fill="{look.face}" stroke="{BLACK}" stroke-width="4"/>'
    return eye


def _mouth(look: Look) -> str:
    kind = look.mouth
    if kind == "sealed":  # Golu: muteness
        stitches = "".join(f'<line x1="{x}" y1="167" x2="{x + 2}" y2="181" stroke="{CREAM}" stroke-width="3"/>' for x in range(74, 127, 10))
        return f'<path d="M66,174 Q100,186 134,174" stroke="{BLACK}" stroke-width="6" fill="none" stroke-linecap="round"/>' + stitches
    if kind == "chatter":  # Jala: chills
        teeth = "".join(f'<rect x="{x}" y="166" width="9" height="15" fill="{CREAM}" stroke="{BLACK}" stroke-width="1.5"/>' for x in range(68, 131, 10))
        return f'<rect x="64" y="162" width="72" height="24" rx="8" fill="{BLACK}"/>' + teeth
    shape = '<path d="M60,164 Q100,158 140,164 Q132,204 100,206 Q68,204 60,164 Z" fill="#5a0f0b" stroke="{b}" stroke-width="4"/>'.format(b=BLACK)
    teeth = "".join(f'<rect x="{x}" y="163" width="10" height="9" fill="{CREAM}"/>' for x in range(72, 125, 11))
    if kind == "open":  # Amukku, Pith: sickness pouring out
        return shape + teeth + f'<path d="M86,186 Q100,222 114,186 Z" fill="{RED}" stroke="{BLACK}" stroke-width="3"/>'
    fangs = (f'<path d="M66,166 L74,166 L69,188 Z" fill="{CREAM}" stroke="{BLACK}" stroke-width="2"/>'
             f'<path d="M126,166 L134,166 L131,188 Z" fill="{CREAM}" stroke="{BLACK}" stroke-width="2"/>')
    if kind == "tusks":
        fangs = (f'<path d="M64,190 Q58,166 70,150 L76,170 Z" fill="{CREAM}" stroke="{BLACK}" stroke-width="2"/>'
                 f'<path d="M136,190 Q142,166 130,150 L124,170 Z" fill="{CREAM}" stroke="{BLACK}" stroke-width="2"/>')
    return shape + teeth + fangs


def _marks(look: Look) -> str:
    out = []
    if "cheeks" in look.marks:  # Vatha, Slesma: swelling
        out += [f'<circle cx="{x}" cy="152" r="17" fill="{RED}" opacity="0.55"/>' for x in (60, 140)]
    if "boils" in look.marks:  # Gedi: skin disease
        out += [f'<circle cx="{x}" cy="{y}" r="{r}" fill="{RED}" stroke="{BLACK}" stroke-width="1.5"/>'
                for x, y, r in ((58, 150, 5), (68, 160, 3.5), (142, 148, 5), (134, 160, 4), (100, 92, 4), (88, 84, 3))]
    if "spots" in look.marks:  # Deva: epidemic
        out += [f'<circle cx="{x}" cy="{y}" r="3" fill="{YELLOW}"/>' for x, y in ((60, 145), (140, 145), (66, 157), (134, 157), (100, 88))]
    if "worms" in look.marks:  # Gulma: worms
        out += [f'<path d="M{x},140 q5,-6 10,0 t10,0 t10,0" fill="none" stroke="{YELLOW}" stroke-width="3.5" stroke-linecap="round"/>' for x in (46, 124)]
    if "swirl" in look.marks:  # Abutha: a mind tied in knots
        out.append(f'<path d="M100,88 m-2,0 a2,2 0 1,1 4,0 a5,5 0 1,1 -9,0 a8,8 0 1,1 15,0" fill="none" stroke="{BLACK}" stroke-width="3"/>')
    if "sweat" in look.marks:  # Gini Jala: fever
        out += [f'<path d="M{x},92 q-5,9 0,12 q5,-3 0,-12 Z" fill="{CREAM}" stroke="{BLACK}" stroke-width="1.5"/>' for x in (64, 138)]
    if "drip" in look.marks:  # Pith, Slesma: bile and phlegm
        out.append(f'<path d="M96,156 q-4,14 4,16 q8,-2 4,-16 Z" fill="{BILE}" stroke="{BLACK}" stroke-width="2"/>')
    if "droop" in look.marks:  # Kora: paralysis, one side sags
        out.append(f'<path d="M126,140 q10,10 4,22" fill="none" stroke="{BLACK}" stroke-width="3"/>')
    return "".join(out)


def _face(look: Look) -> str:
    ink = CREAM if look.face == BLACK else BLACK  # dark faces need light carving lines
    brows = (f'<path d="M52,98 Q72,80 94,96" stroke="{ink}" stroke-width="8" fill="none" stroke-linecap="round"/>'
             f'<path d="M106,96 Q128,80 148,98" stroke="{ink}" stroke-width="8" fill="none" stroke-linecap="round"/>')
    nose = f'<path d="M92,128 Q88,150 100,152 Q112,150 108,128" fill="{look.face}" stroke="{ink}" stroke-width="4"/>'
    return (
        _ears(look)
        + f'<ellipse cx="100" cy="132" rx="62" ry="74" fill="{look.face}" stroke="{ink}" stroke-width="5"/>'
        + '<ellipse cx="82" cy="100" rx="22" ry="12" fill="#ffffff" opacity="0.12"/>'
        + brows + _eye(76, 116, look) + _eye(124, 116, look) + nose + _mouth(look) + _marks(look)
    )


def _svg(body: str, label: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 215" role="img" aria-label="{label}">'
            f"<title>{label}</title>{body}</svg>")


def mask_svg(demon: str) -> str:
    look = LOOKS[demon]
    return _svg(_crown(look) + _face(look), f"{demon} Sanniya mask")


def kola_svg() -> str:
    """Kola Sanniya, the leader, carries the 18 small demon faces around his own."""
    import math

    ring = []
    for i, name in enumerate(LOOKS):
        angle = math.radians(160 + i * (220 / 17))
        x, y = 100 + 84 * math.cos(angle), 122 + 92 * math.sin(angle)
        look = LOOKS[name]
        ring.append(
            f'<g><circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="{look.face}" stroke="{BLACK}" stroke-width="2.5"/>'
            f'<circle cx="{x - 3.5:.1f}" cy="{y - 1.5:.1f}" r="2.4" fill="{CREAM}"/><circle cx="{x + 3.5:.1f}" cy="{y - 1.5:.1f}" r="2.4" fill="{CREAM}"/>'
            f'<path d="M{x - 4:.1f},{y + 4:.1f} Q{x:.1f},{y + 7:.1f} {x + 4:.1f},{y + 4:.1f}" stroke="{BLACK}" stroke-width="1.6" fill="none"/></g>'
        )
    kola = Look(face=GREEN, crown=RED, crown_kind="none", mouth="tusks")
    face = f'<g transform="translate(100 128) scale(0.8) translate(-100 -128)">{_face(kola)}</g>'
    return _svg("".join(ring) + face, "Kola Sanniya mask")
