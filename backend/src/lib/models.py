"""Pydantic v2 models for AI output and API request bodies."""
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Role = Literal["household", "picker", "recycler", "city"]
Language = Literal["en", "hi"]
ID_PATTERN = r"^[A-Za-z0-9_\-]+$"


class VisionItem(BaseModel):
    """One item group as returned by the vision model (validated loosely, cleaned in code)."""

    model_config = ConfigDict(extra="ignore")

    name: str = "item"
    material: str = "OTHER_LANDFILL"
    count: int = 1
    estWeightKg: float = 0.0
    brand: Optional[str] = None

    @field_validator("name", mode="before")
    @classmethod
    def _name(cls, v: object) -> str:
        return str(v or "item")[:200]

    @field_validator("material", mode="before")
    @classmethod
    def _material(cls, v: object) -> str:
        return str(v or "OTHER_LANDFILL")

    @field_validator("count", mode="before")
    @classmethod
    def _count(cls, v: object) -> int:
        try:
            return max(1, int(round(float(v))))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 1

    @field_validator("estWeightKg", mode="before")
    @classmethod
    def _weight(cls, v: object) -> float:
        try:
            return float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0.0

    @field_validator("brand", mode="before")
    @classmethod
    def _brand(cls, v: object) -> Optional[str]:
        if v is None:
            return None
        text = str(v).strip()
        if not text or text.lower() in {"null", "none", "unknown", "n/a", "unbranded"}:
            return None
        return text[:60]


class VisionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    isWasteImage: bool
    segregationScore: int = 0
    tip: str = ""
    items: list[VisionItem] = Field(default_factory=list)

    @field_validator("segregationScore", mode="before")
    @classmethod
    def _score(cls, v: object) -> int:
        try:
            return min(100, max(0, int(round(float(v)))))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0

    @field_validator("tip", mode="before")
    @classmethod
    def _tip(cls, v: object) -> str:
        return str(v or "")[:300]


class _Body(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)


class CreateUserRequest(_Body):
    name: str = Field(min_length=1, max_length=80)
    role: Role
    societyId: Optional[str] = Field(default=None, max_length=64, pattern=ID_PATTERN)
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lng: Optional[float] = Field(default=None, ge=-180, le=180)
    language: Language = "en"


class UploadRequest(_Body):
    userId: str = Field(min_length=1, max_length=64, pattern=ID_PATTERN)
    contentType: str = Field(max_length=100)


class ScanRequest(_Body):
    userId: str = Field(min_length=1, max_length=64, pattern=ID_PATTERN)
    imageKey: str = Field(min_length=1, max_length=300)


class RateUpdateRequest(_Body):
    userId: str = Field(min_length=1, max_length=64, pattern=ID_PATTERN)
    rsPerKg: float = Field(ge=0, le=500)


class PickerRequest(_Body):
    pickerId: str = Field(min_length=1, max_length=64, pattern=ID_PATTERN)


class CoachRequest(_Body):
    userId: str = Field(min_length=1, max_length=64, pattern=ID_PATTERN)
    language: Language = "en"
