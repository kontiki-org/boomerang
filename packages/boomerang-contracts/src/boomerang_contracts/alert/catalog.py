from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# RPC implemented by each alert connector; aggregated by subscription-service.
GET_ALERT_SUBSCRIPTION_CATALOG_RPC = "get_alert_subscription_catalog"

CriterionOperator = Literal["eq", "gte", "lte", "contains"]
CriterionValueKind = Literal["number", "string", "boolean"]


class AlertCriterionDescriptor(BaseModel):
    """Describes one subscription criterion exposed to clients."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    operators: list[CriterionOperator] = Field(min_length=1)
    value_kind: CriterionValueKind
    attribute_key: str | None = None

    @model_validator(mode="after")
    def _normalize(self) -> "AlertCriterionDescriptor":
        self.key = self.key.strip().lower()
        self.label = self.label.strip()
        if self.attribute_key is None:
            self.attribute_key = self.key
        else:
            self.attribute_key = self.attribute_key.strip().lower()
        if not self.key or not self.label or not self.attribute_key:
            raise ValueError("Invalid catalog criterion.")
        return self


class AlertEventTypeCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(min_length=1)
    label: str = Field(min_length=1)
    criteria: list[AlertCriterionDescriptor] = Field(default_factory=list)

    @model_validator(mode="after")
    def _normalize(self) -> "AlertEventTypeCatalog":
        self.event_type = self.event_type.strip().lower()
        self.label = self.label.strip()
        if not self.event_type or not self.label:
            raise ValueError("Invalid catalog event type.")
        return self


class AlertCategoryCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1)
    label: str = Field(min_length=1)
    event_types: list[AlertEventTypeCatalog] = Field(min_length=1)

    @model_validator(mode="after")
    def _normalize(self) -> "AlertCategoryCatalog":
        self.category = self.category.strip().lower()
        self.label = self.label.strip()
        if not self.category or not self.label or not self.event_types:
            raise ValueError("Invalid catalog category.")
        return self


class AlertConnectorCatalog(BaseModel):
    """Catalog returned by a single alert connector RPC."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    categories: list[AlertCategoryCatalog] = Field(min_length=1)

    @model_validator(mode="after")
    def _normalize(self) -> "AlertConnectorCatalog":
        self.source_id = self.source_id.strip()
        if not self.source_id or not self.categories:
            raise ValueError("Invalid connector catalog.")
        return self


class AlertSubscriptionCatalog(BaseModel):
    """Catalog aggregated by subscription-service for UI and clients."""

    model_config = ConfigDict(extra="forbid")

    sources: list[AlertConnectorCatalog] = Field(default_factory=list)
