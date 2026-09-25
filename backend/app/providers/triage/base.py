from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas import Category, Priority


class TriageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Category
    priority: Priority
    summary: str = Field(min_length=1, max_length=140)
    confidence: float = Field(ge=0, le=1)

    @field_validator("summary")
    @classmethod
    def require_single_line(cls, value: str) -> str:
        if "\n" in value or "\r" in value:
            raise ValueError("Summary must be a single line")
        if not value.strip():
            raise ValueError("Summary must not be blank")
        return value


class TriageProvider(Protocol):
    name: str

    def triage(self, text: str, location: str) -> TriageResult: ...
