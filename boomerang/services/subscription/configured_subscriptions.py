from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from boomerang.core.contracts.subscription import RuleDefinition
from boomerang.services.subscription.subscription_resolution import (
    build_facts_from_alert,
    criteria_matches,
    rule_matches_alert,
    sort_recipients,
)


class QualifiedEndpointRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: str = Field(min_length=1)
    endpoint_id: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def _parse_qualified_ref(cls, value: Any) -> Any:
        if isinstance(value, str):
            parts = value.split(".", 1)
            if len(parts) != 2:
                raise ValueError("Invalid endpoint ref.")
            channel = parts[0].strip().lower()
            endpoint_id = parts[1].strip()
            if not channel or not endpoint_id:
                raise ValueError("Invalid endpoint ref.")
            return {"channel": channel, "endpoint_id": endpoint_id}
        raise ValueError("Invalid endpoint ref.")

    @model_validator(mode="after")
    def _normalize(self) -> "QualifiedEndpointRef":
        self.channel = self.channel.strip().lower()
        self.endpoint_id = self.endpoint_id.strip()
        if not self.channel or not self.endpoint_id:
            raise ValueError("Invalid endpoint ref.")
        return self


class ConfiguredSubscriptionBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule: RuleDefinition
    endpoints: list[QualifiedEndpointRef] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_unique_endpoints(self) -> "ConfiguredSubscriptionBody":
        seen: set[tuple[str, str]] = set()
        for endpoint in self.endpoints:
            key = (endpoint.channel, endpoint.endpoint_id.lower())
            if key in seen:
                raise ValueError("Invalid endpoint ref.")
            seen.add(key)
        return self


class ConfiguredSubscriptionEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["active", "paused"]
    subscription: ConfiguredSubscriptionBody


class ConfiguredSubscriptionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_id: str = Field(min_length=1)
    rule_name: str = Field(min_length=1)
    status: Literal["active", "paused"]
    subscription: ConfiguredSubscriptionBody


class ConfiguredSubscriptionStore:
    def __init__(self, records: list[ConfiguredSubscriptionRecord]):
        self._records = records

    def __len__(self) -> int:
        return len(self._records)

    def get_recipients_for_alert(self, alert: dict) -> list[dict]:
        category, event_type, facts = build_facts_from_alert(alert)
        if not category or not event_type:
            return []

        targets: list[dict] = []
        for record in self._records:
            if record.status != "active":
                continue
            rule = record.subscription.rule
            if not rule_matches_alert(rule.category, rule.event_type, category, event_type):
                continue
            if not criteria_matches(rule.criteria.model_dump(), facts):
                continue
            for endpoint in record.subscription.endpoints:
                targets.append(
                    {
                        "recipient_id": record.owner_id,
                        "channel": endpoint.channel,
                        "endpoint_key": endpoint.endpoint_id,
                    }
                )
        return sort_recipients(targets)


def load_configured_subscriptions(raw: object) -> ConfiguredSubscriptionStore:
    if raw is None:
        return ConfiguredSubscriptionStore([])
    if not isinstance(raw, dict):
        raise RuntimeError("Invalid app.subscriptions configuration.")

    records: list[ConfiguredSubscriptionRecord] = []
    for owner_id, rules in raw.items():
        owner = str(owner_id).strip()
        if not owner:
            raise RuntimeError(
                "Invalid app.subscriptions configuration: empty owner_id."
            )
        if not isinstance(rules, dict):
            raise RuntimeError(
                f"Invalid app.subscriptions configuration for owner {owner!r}."
            )
        for rule_name, entry_raw in rules.items():
            rule_key = str(rule_name).strip()
            if not rule_key:
                raise RuntimeError(
                    "Invalid app.subscriptions configuration: "
                    f"empty rule name under owner {owner!r}."
                )
            try:
                entry = ConfiguredSubscriptionEntry.model_validate(entry_raw)
            except ValidationError as exc:
                raise RuntimeError(
                    "Invalid app.subscriptions configuration for "
                    f"{owner!r}.{rule_key}: {exc}"
                ) from exc
            records.append(
                ConfiguredSubscriptionRecord(
                    owner_id=owner,
                    rule_name=rule_key,
                    status=entry.status,
                    subscription=entry.subscription,
                )
            )
    return ConfiguredSubscriptionStore(records)
