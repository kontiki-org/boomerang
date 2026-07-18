from __future__ import annotations

import re

from boomerang.core.contracts.notification.channel_catalog import (
    NotificationChannelCatalog,
)
from boomerang.core.exceptions import ValidationError
from boomerang.core.contracts.notification.validation import validate_endpoint_fields

_CHAT_ID_RE = re.compile(r"-?\d+")


class ConfiguredEndpointStore:
    def __init__(self, endpoints: dict[str, dict[str, str]]):
        self._endpoints = endpoints

    def __len__(self) -> int:
        return len(self._endpoints)

    def get(self, endpoint_id: str) -> dict[str, str] | None:
        key = (endpoint_id or "").strip()
        if not key:
            return None
        return self._endpoints.get(key)


def load_configured_endpoints(
    raw: object,
    catalog: NotificationChannelCatalog,
) -> ConfiguredEndpointStore:
    if raw is None:
        return ConfiguredEndpointStore({})
    if not isinstance(raw, dict):
        raise RuntimeError("Invalid app.endpoints configuration.")

    endpoints: dict[str, dict[str, str]] = {}
    for endpoint_id, fields_raw in raw.items():
        key = str(endpoint_id).strip()
        if not key:
            raise RuntimeError(
                "Invalid app.endpoints configuration: empty endpoint_id."
            )
        if not isinstance(fields_raw, dict):
            raise RuntimeError(
                f"Invalid app.endpoints configuration for endpoint {key!r}."
            )
        try:
            string_fields = {
                str(field_key): str(value) for field_key, value in fields_raw.items()
            }
            fields = validate_endpoint_fields(catalog, string_fields)
        except ValidationError as exc:
            raise RuntimeError(
                f"Invalid app.endpoints configuration for endpoint {key!r}."
            ) from exc
        chat_id = fields.get("chat_id", "")
        if not _CHAT_ID_RE.fullmatch(chat_id):
            raise RuntimeError(
                f"Invalid app.endpoints configuration for endpoint {key!r}: invalid chat_id."
            )
        endpoints[key] = fields
    return ConfiguredEndpointStore(endpoints)
