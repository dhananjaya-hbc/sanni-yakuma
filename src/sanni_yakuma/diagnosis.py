"""What Gemma must answer, and the finished ritual we build from it."""

from pydantic import BaseModel, Field

from .omen import Omen


class Patch(BaseModel):
    """One find/replace edit, as Gemma writes it."""

    path: str
    find: str
    replace: str


class Exorcism(BaseModel):
    summary: str
    steps: list[str] = Field(min_length=1, max_length=6)
    patch: Patch | None = None
    # Built by us from the patch with difflib; Gemma never writes it.
    diff: str | None = None


class Possession(BaseModel):
    demon: str
    severity: int = Field(ge=1, le=3)
    evidence_ids: list[str] = Field(min_length=1)
    monologue: str
    exorcism: Exorcism


class Blessing(BaseModel):
    title: str
    detail: str


class KolaVerdict(BaseModel):
    root_cause: str
    explanation: str
    verse_sinhala: str
    verse_transliteration: str
    verse_english: str


class GemmaAnswer(BaseModel):
    """The JSON Gemma returns, exactly as the prompt asks for it."""

    blessings: list[Blessing] = Field(max_length=8)
    possessions: list[Possession]
    kola_sanniya: KolaVerdict


class Ritual(BaseModel):
    """Everything the ritual page needs."""

    repo: str
    url: str | None
    model: str
    performed_at: str
    omens: list[Omen]
    blessings: list[Blessing]
    possessions: list[Possession]
    # Demons the detectors suspected but Gemma judged harmless, and claims we threw out.
    spared: list[str] = []
    rejected: list[str] = []
    kola_sanniya: KolaVerdict
