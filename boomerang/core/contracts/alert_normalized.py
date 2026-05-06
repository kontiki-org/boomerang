from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AlertArea(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1)
    value: str = Field(min_length=1)

    @model_validator(mode="after")
    def _normalize(self) -> "AlertArea":
        normalized_type = self.type.strip().lower()
        normalized_value = self.value.strip()
        if not normalized_type or not normalized_value:
            raise ValueError("Invalid request payload.")
        self.type = normalized_type
        self.value = normalized_value
        return self


class NormalizedAlert(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="1.0")
    alert_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    category: str = Field(min_length=1)
    event_type: str = Field(default="*")
    severity: str = Field(default="unknown")
    occurred_at: datetime
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    areas: list[AlertArea] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def _normalize(self) -> "NormalizedAlert":
        self.alert_id = self.alert_id.strip()
        self.source = self.source.strip()
        self.category = self.category.strip().lower()
        self.event_type = (self.event_type or "*").strip().lower() or "*"
        self.severity = (self.severity or "unknown").strip().lower() or "unknown"
        self.title = self.title.strip()
        self.body = self.body.strip()
        if (
            not self.alert_id
            or not self.source
            or not self.category
            or not self.title
            or not self.body
        ):
            raise ValueError("Invalid request payload.")
        return self
