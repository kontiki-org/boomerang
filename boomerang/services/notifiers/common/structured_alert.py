"""Shared structured-alert content for notifier formatters (telegram, email)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from boomerang_contracts.notification.message import NotificationMessage

_URL_RE = re.compile(r"https?://[^\s]+")

SEVERITY_ICONS = {
    "low": "🟢",
    "moderate": "🟡",
    "severe": "🟠",
    "critical": "🔴",
    "unknown": "⚪",
}


@dataclass(frozen=True)
class StructuredAlertParts:
    category: str
    event_type: str
    severity: str
    banner_label: str
    title: str
    message: str
    attributes: tuple[tuple[str, str], ...]
    detail_url: str


def parse_structured_alert(message: NotificationMessage):
    title = message.title.strip()
    body = message.body.strip()
    context = message.context
    data = context.data if context is not None else {}

    category = as_text(data.get("category")).lower()
    is_alert = category or (
        context is not None and context.kind.strip().lower() == "alert"
    )
    if not is_alert:
        return None

    event_type = as_text(data.get("event_type")).lower()
    severity = as_text(data.get("severity")).lower() or "unknown"
    attributes = normalize_attributes(data.get("attributes"))
    detail_url = detail_url_from(attributes, body)
    summary = summary_without_url(body, attributes)
    message_text = ""
    if summary and summary != title:
        message_text = summary

    attr_rows = []
    for key, value in attributes.items():
        if key == "url" or value is None or value == "":
            continue
        attr_rows.append((humanize_key(key), format_value(value)))

    return StructuredAlertParts(
        category=category,
        event_type=event_type,
        severity=severity,
        banner_label=resolve_banner_label(category, event_type),
        title=title,
        message=message_text,
        attributes=tuple(attr_rows),
        detail_url=detail_url,
    )


def resolve_category_icon(category, category_icons):
    if not category or not category_icons:
        return ""
    if category in category_icons:
        return category_icons[category]

    for prefix, icon in category_icons.items():
        if category.startswith(f"{prefix}.") or category.startswith(prefix):
            return icon
    return ""


def resolve_banner_label(category, event_type):
    if event_type and event_type != "*":
        return humanize_key(event_type)
    if category:
        return humanize_key(category.split(".")[-1])
    return "Alert"


def detail_url_from(attributes, body):
    url = attributes.get("url")
    if isinstance(url, str) and url.startswith(("http://", "https://")):
        return url.strip()

    match = _URL_RE.search(body)
    if match:
        return match.group(0).rstrip(").,]")
    return ""


def summary_without_url(body, attributes):
    detail_url = detail_url_from(attributes, body)
    if not body:
        return ""

    cleaned = body
    if detail_url:
        cleaned = cleaned.replace(detail_url, "")
    cleaned = cleaned.replace("Detail:", "").strip()
    if detail_url:
        cleaned = cleaned.rstrip(" .\n")
    if not cleaned:
        return ""
    return cleaned


def normalize_attributes(raw):
    if not isinstance(raw, dict):
        return {}
    normalized = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        normalized_key = key.strip().lower()
        if normalized_key:
            normalized[normalized_key] = value
    return normalized


def format_value(value):
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)
    return str(value)


def humanize_key(key):
    return key.replace("_", " ").strip().title()


def as_text(value):
    if value is None:
        return ""
    return str(value).strip()


def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def normalize_category_icons(raw: Any):
    if not isinstance(raw, dict):
        return {}
    normalized = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        normalized_key = key.strip().lower()
        icon = "" if value is None else str(value).strip()
        if normalized_key and icon:
            normalized[normalized_key] = icon
    return normalized
