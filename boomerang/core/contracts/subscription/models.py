from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# Subscription contracts (target model)


class EndpointRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str = Field(min_length=1)
    endpoint_key: str = Field(min_length=1)

    @model_validator(mode="after")
    def _normalize(self) -> "EndpointRef":
        normalized_kind = self.kind.strip().lower()
        normalized_endpoint_key = self.endpoint_key.strip()
        if not normalized_kind or not normalized_endpoint_key:
            raise ValueError("Invalid request payload.")
        self.kind = normalized_kind
        self.endpoint_key = normalized_endpoint_key
        return self


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


class CriteriaExpression(BaseModel):
    model_config = ConfigDict(extra="forbid")

    all_of: list[Criterion] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_not_empty(self) -> "CriteriaExpression":
        if not self.all_of:
            raise ValueError("Invalid request payload.")
        return self


class RuleDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1)
    event_type: str = Field(default="*")
    criteria: CriteriaExpression

    @model_validator(mode="after")
    def _normalize(self) -> "RuleDefinition":
        normalized_category = self.category.strip().lower()
        normalized_event_type = self.event_type.strip().lower()
        if not normalized_category:
            raise ValueError("Invalid request payload.")
        self.category = normalized_category
        self.event_type = normalized_event_type or "*"
        return self


class SubscriptionDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule: RuleDefinition
    endpoints: list[EndpointRef] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_unique_endpoints(self) -> "SubscriptionDefinition":
        seen: set[tuple[str, str]] = set()
        for endpoint in self.endpoints:
            key = (endpoint.kind, endpoint.endpoint_key.lower())
            if key in seen:
                raise ValueError("Invalid request payload.")
            seen.add(key)
        return self


class CreateSubscriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subscription: SubscriptionDefinition


class UpdateSubscriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule: RuleDefinition | None = None
    endpoints: list[EndpointRef] | None = None
    status: Literal["active", "paused"] | None = None

    @model_validator(mode="after")
    def _validate_non_empty_update(self) -> "UpdateSubscriptionRequest":
        if self.rule is None and self.endpoints is None and self.status is None:
            raise ValueError("Invalid request payload.")
        if self.endpoints is not None and len(self.endpoints) == 0:
            raise ValueError("Invalid request payload.")
        return self
