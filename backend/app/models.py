"""Request / response models with strict validation (unknown fields are rejected)."""
import re
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .fields import STATES

KEY_RE = re.compile(r"^[a-z][a-z_]{1,39}$")
LONG_DIGITS = re.compile(r"\d[\d\s-]{9,}\d")

_STATE_LOOKUP = {s.lower(): s for s in STATES}


class Profile(BaseModel):
    """Minimal eligibility profile. Deliberately has NO fields for Aadhaar, bank numbers or passwords."""
    model_config = ConfigDict(extra="forbid")

    age: Optional[int] = Field(None, ge=0, le=120)
    state: Optional[str] = None
    district: Optional[str] = Field(None, max_length=60)
    annual_income: Optional[int] = Field(None, ge=0, le=1_000_000_000)
    occupation: Optional[Literal["student", "farmer", "salaried", "self_employed", "unemployed", "homemaker", "retired", "other"]] = None
    education_level: Optional[Literal["below_class_10", "class_10", "class_12", "undergraduate", "postgraduate", "doctorate"]] = None
    is_student: Optional[bool] = None
    gender: Optional[Literal["female", "male", "other"]] = None
    category: Optional[Literal["general", "ews", "obc", "sc", "st", "ebc_dnt"]] = None
    employment_status: Optional[Literal["employed", "self_employed", "underemployed", "unemployed"]] = None
    business_status: Optional[Literal["none", "planning", "running"]] = None
    landholding_hectares: Optional[float] = Field(None, ge=0, le=100000)
    land_tenure: Optional[Literal["owner", "tenant", "none"]] = None
    existing_benefits: Optional[list[str]] = Field(None, max_length=20)
    documents: dict[str, Literal["available", "missing"]] = Field(default_factory=dict)
    language: Literal["en", "hi"] = "en"

    @field_validator("state")
    @classmethod
    def _state(cls, v):
        if v is None or v == "":
            return None
        canon = _STATE_LOOKUP.get(v.strip().lower())
        if not canon:
            raise ValueError("unknown state or union territory")
        return canon

    @field_validator("district")
    @classmethod
    def _district(cls, v):
        if v is None:
            return None
        v = v.strip()
        if LONG_DIGITS.search(v):
            raise ValueError("this field must not contain ID or account numbers")
        return v or None

    @field_validator("existing_benefits")
    @classmethod
    def _benefits(cls, v):
        if v is None:
            return None
        for item in v:
            if not KEY_RE.match(item):
                raise ValueError("invalid benefit key")
        return v

    @field_validator("documents")
    @classmethod
    def _docs(cls, v):
        if len(v) > 30:
            raise ValueError("too many document entries")
        for k in v:
            if not KEY_RE.match(k):
                raise ValueError("invalid document key")
        return v

    def eval_dict(self) -> dict:
        d = self.model_dump()
        if d.get("state"):
            d["state"] = d["state"].lower()
        return d


class Filters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: Optional[str] = Field(None, max_length=60)
    category: Optional[str] = Field(None, max_length=40)
    target_group: Optional[str] = Field(None, max_length=40)
    scheme_type: Optional[str] = Field(None, max_length=40)


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field("", max_length=500)
    filters: Filters = Field(default_factory=Filters)
    profile: Optional[Profile] = None
    language: Literal["en", "hi"] = "en"
    limit: int = Field(10, ge=1, le=20)


class AssessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile: Profile = Field(default_factory=Profile)
    language: Literal["en", "hi"] = "en"
    doc_ids: Optional[list[str]] = Field(None, max_length=10)


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(..., min_length=2, max_length=500)
    scheme_id: Optional[str] = Field(None, max_length=60)
    language: Literal["en", "hi"] = "en"


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: str = Field(..., max_length=60)
    args: dict = Field(default_factory=dict)


class AgentRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field("", max_length=500)
    filters: Filters = Field(default_factory=Filters)
    profile: Optional[Profile] = None
    language: Literal["en", "hi"] = "en"
    max_schemes: int = Field(3, ge=1, le=5)
