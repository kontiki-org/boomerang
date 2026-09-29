from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Shared rule/criteria models used by YAML configured subscriptions.


class Criterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1)
    operator: Literal["eq", "gte", "lte", "contains"]
    value: Any

    @model_validator(mode="after")
    def _normalize(self) -> "Criterion":
        normalized_key = self.key.strip().lower()
        if not normalized_key:
            raise ValueError("Invalid request payload.")
        self.key = normalized_key
        return self


class RuleDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1)
    event_type: str = Field(default="*")
    criteria: list[Criterion] | None = None

    @model_validator(mode="after")
    def _normalize(self) -> "RuleDefinition":
        normalized_category = self.category.strip().lower()
        normalized_event_type = self.event_type.strip().lower()
        if not normalized_category:
            raise ValueError("Invalid request payload.")
        if self.criteria is not None and not self.criteria:
            raise ValueError("Invalid request payload.")
        self.category = normalized_category
        self.event_type = normalized_event_type or "*"
        return self
