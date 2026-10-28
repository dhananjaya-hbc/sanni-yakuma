"""Evidence models shared by all detectors.

An Omen is what one detector reports about one demon. It holds only facts
(file, line, snippet, numbers), so the model cannot invent demons later.
"""

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    path: str | None = None
    line: int | None = None
    snippet: str | None = None
    note: str | None = None


class Omen(BaseModel):
    demon: str
    sickness: str
    found: bool
    # 0 = absent, 1 = mild, 2 = clear, 3 = severe. Gemma makes the final call.
    severity_hint: int = Field(ge=0, le=3)
    summary: str
    metrics: dict[str, int | float | str | bool | None] = {}
    evidence: list[Evidence] = []
