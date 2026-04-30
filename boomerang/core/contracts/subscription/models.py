from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AreaSelector(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    value: str

    @model_validator(mode="after")
    def _normalize(self) -> "AreaSelector":
        # Normalize input values to a stable format and reject empty strings.
        normalized_type = self.type.strip().lower()
        normalized_value = self.value.strip()
        if not normalized_type or not normalized_value:
            raise ValueError("Invalid request payload.")

        self.type = normalized_type
        self.value = normalized_value
        return self


class Selectors(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categories: list[str] = Field(min_length=1)
    event_types: list[str] = Field(default_factory=list)
    areas: list[AreaSelector] = Field(default_factory=list)
    min_severity: str = "moderate"

    @model_validator(mode="after")
    def _normalize(self) -> "Selectors":
        # Normalize identity fields early to keep comparisons/idempotency consistent.
        normalized_categories = [item.strip().lower() for item in self.categories]
        normalized_event_types = [item.strip().lower() for item in self.event_types]
        normalized_min_severity = self.min_severity.strip().lower()
        if not normalized_event_types:
            # Align with API behavior: empty list means wildcard.
            normalized_event_types = ["*"]

        if any(not item for item in normalized_categories):
            raise ValueError("Invalid request payload.")
        if any(not item for item in normalized_event_types):
            raise ValueError("Invalid request payload.")
        if not normalized_min_severity:
            raise ValueError("Invalid request payload.")
        if not self.areas:
            # Keep identity tuple stable for non-geographic subscriptions.
            self.areas = [AreaSelector(type="global", value="*")]

        self.categories = normalized_categories
        self.event_types = normalized_event_types
        self.min_severity = normalized_min_severity
        return self


class DeliveryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channels: list[str] | None = None
    fallback_to_default_channels: bool = True

    @model_validator(mode="after")
    def _normalize(self) -> "DeliveryConfig":
        # Normalize optional channels while preserving a missing channels payload.
        if self.channels is None:
            return self

        normalized_channels = [item.strip().lower() for item in self.channels]
        if any(not item for item in normalized_channels):
            raise ValueError("Invalid request payload.")

        self.channels = normalized_channels
        return self


class QuietHours(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    start: str | None = None
    end: str | None = None
    timezone: str | None = None

    @model_validator(mode="after")
    def _validate_enabled_requirements(self) -> "QuietHours":
        # Enforce required quiet-hours fields only when the option is enabled.
        if not self.enabled:
            return self

        start = (self.start or "").strip()
        end = (self.end or "").strip()
        tz = (self.timezone or "").strip()
        if not start or not end or not tz:
            raise ValueError("Invalid request payload.")

        self.start = start
        self.end = end
        self.timezone = tz
        return self


class PolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quiet_hours: QuietHours = Field(default_factory=QuietHours)


class CreateSubscriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selectors: Selectors
    delivery: DeliveryConfig = Field(default_factory=DeliveryConfig)
    policy: PolicyConfig = Field(default_factory=PolicyConfig)


class UpdateSubscriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_severity: str | None = None
    policy: PolicyConfig | None = None
    status: str | None = None

    @model_validator(mode="after")
    def _normalize(self) -> "UpdateSubscriptionRequest":
        if self.min_severity is not None:
            normalized_min_severity = self.min_severity.strip().lower()
            if not normalized_min_severity:
                raise ValueError("Invalid request payload.")
            self.min_severity = normalized_min_severity

        if self.status is not None:
            normalized_status = self.status.strip().lower()
            if normalized_status not in {"active", "paused"}:
                raise ValueError("Invalid request payload.")
            self.status = normalized_status

        if self.min_severity is None and self.policy is None and self.status is None:
            raise ValueError("Invalid request payload.")

        return self
