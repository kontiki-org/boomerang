from __future__ import annotations

import re
from urllib.parse import urlparse

from boomerang_contracts.exceptions import ValidationError
from boomerang_contracts.notification.channel_catalog import (
    ChannelFieldDescriptor,
    NotificationChannelCatalog,
)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_endpoint_fields(
    catalog: NotificationChannelCatalog,
    fields: dict[str, str],
) -> dict[str, str]:
    descriptors = {descriptor.key: descriptor for descriptor in catalog.fields}
    if not descriptors:
        raise ValidationError()

    normalized: dict[str, str] = {}
    for key, value in fields.items():
        normalized_key = (key or "").strip().lower()
        normalized_value = (value or "").strip()
        if normalized_key in descriptors and normalized_value:
            normalized[normalized_key] = normalized_value

    for descriptor in catalog.fields:
        value = normalized.get(descriptor.key, "")
        if descriptor.required and not value:
            raise ValidationError()
        if value:
            normalized[descriptor.key] = _normalize_field_value(descriptor, value)

    extra_keys = set(normalized) - set(descriptors)
    if extra_keys:
        raise ValidationError()

    return normalized


def endpoint_display(
    catalog: NotificationChannelCatalog,
    fields: dict[str, str],
) -> str:
    summary_key = catalog.summary_field or catalog.fields[0].key
    return fields.get(summary_key, "")


def _normalize_field_value(descriptor: ChannelFieldDescriptor, value: str) -> str:
    if descriptor.field_type == "email":
        normalized = value.strip().lower()
        if not _EMAIL_RE.match(normalized):
            raise ValidationError()
        return normalized

    if descriptor.field_type == "url":
        parsed = urlparse(value.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValidationError()
        return value.strip()

    if descriptor.field_type == "number":
        try:
            float(value.strip())
        except ValueError as exc:
            raise ValidationError() from exc
        return value.strip()

    if descriptor.field_type == "choice":
        allowed = {choice.value for choice in descriptor.choices or []}
        if value not in allowed:
            raise ValidationError()
        return value

    return value.strip()
