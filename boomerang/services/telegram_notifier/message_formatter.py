import re
from typing import Any

from boomerang_contracts.notification.message import NotificationMessage

_URL_RE = re.compile(r"https?://[^\s]+")

_CATEGORY_DISPLAY: dict[str, tuple[str, str]] = {
    "natural.earthquake": ("🌍", "Earthquake"),
    "weather": ("🌧", "Weather"),
    "wildfire": ("🔥", "Wildfire"),
    "safety.fire": ("🔥", "Wildfire"),
    "website": ("🌐", "Website"),
    "kontiki.registry": ("⚙️", "Kontiki Registry"),
    "certificate": ("🔒", "Certificate"),
}

_EVENT_TYPE_DISPLAY: dict[str, tuple[str, str]] = {
    "earthquake": ("🌍", "Earthquake"),
    "wildfire": ("🔥", "Wildfire"),
}

_SEVERITY_ICONS: dict[str, str] = {
    "low": "🟢",
    "moderate": "🟡",
    "severe": "🟠",
    "critical": "🔴",
    "unknown": "⚪",
}

_ATTRIBUTE_LABELS: dict[str, str] = {
    "magnitude": "Magnitude",
    "place": "Location",
    "region": "Region",
    "response_time": "Response time",
    "status_code": "Status code",
    "service": "Service",
    "previous_state": "Previous state",
    "new_state": "New state",
}

_ATTRIBUTE_ORDER: tuple[str, ...] = (
    "magnitude",
    "place",
    "region",
    "response_time",
    "status_code",
    "service",
    "previous_state",
    "new_state",
)


def format_telegram_notification(
    message: NotificationMessage,
) -> tuple[str, str | None]:
    title = message.title.strip()
    body = message.body.strip()
    context = message.context
    data = context.data if context is not None else {}

    category = _as_text(data.get("category")).lower()
    if category or (context is not None and context.kind.strip().lower() == "alert"):
        return _format_structured_alert(
            title=title,
            body=body,
            category=category,
            event_type=_as_text(data.get("event_type")).lower(),
            severity=_as_text(data.get("severity")).lower() or "unknown",
            attributes=_normalize_attributes(data.get("attributes")),
        )

    if title and body:
        return f"{title}\n\n{body}", None
    return title or body, None


def _format_structured_alert(
    *,
    title: str,
    body: str,
    category: str,
    event_type: str,
    severity: str,
    attributes: dict[str, Any],
) -> tuple[str, str | None]:
    category_icon, category_label = _resolve_category_display(category, event_type)
    severity_icon = _SEVERITY_ICONS.get(severity, _SEVERITY_ICONS["unknown"])

    lines = [
        f"{category_icon} {severity_icon} <b>{_escape_html(category_label)}</b>",
        "",
    ]

    metadata_lines = _metadata_lines(attributes)
    if metadata_lines:
        lines.extend(metadata_lines)
        lines.append("")
    elif title:
        lines.append(_escape_html(title))
        lines.append("")

    if not metadata_lines:
        summary = _summary_without_url(body, attributes)
        if summary and summary != title:
            lines.append(_escape_html(summary))
            lines.append("")

    detail_url = _detail_url(attributes, body)
    if detail_url:
        safe_url = _escape_html(detail_url)
        lines.append(f'🔗 <a href="{safe_url}">Details</a>')

    text = "\n".join(line for line in lines if line is not None).strip()
    return text, "HTML"


def _metadata_lines(attributes: dict[str, Any]) -> list[str]:
    if not attributes:
        return []

    lines = []
    seen = set()
    for key in _ATTRIBUTE_ORDER:
        if key not in attributes or key == "url":
            continue
        value = attributes[key]
        if value is None or value == "":
            continue
        label = _ATTRIBUTE_LABELS.get(key, _humanize_key(key))
        lines.append(
            f"<b>{_escape_html(label)}:</b> {_escape_html(_format_value(value))}"
        )
        seen.add(key)

    for key in sorted(attributes):
        if key in seen or key == "url":
            continue
        value = attributes[key]
        if value is None or value == "":
            continue
        label = _ATTRIBUTE_LABELS.get(key, _humanize_key(key))
        lines.append(
            f"<b>{_escape_html(label)}:</b> {_escape_html(_format_value(value))}"
        )

    return lines


def _resolve_category_display(category: str, event_type: str) -> tuple[str, str]:
    if category in _CATEGORY_DISPLAY:
        return _CATEGORY_DISPLAY[category]

    for prefix, display in _CATEGORY_DISPLAY.items():
        if category.startswith(f"{prefix}.") or category.startswith(prefix):
            return display

    if event_type in _EVENT_TYPE_DISPLAY:
        return _EVENT_TYPE_DISPLAY[event_type]

    if category:
        label = category.split(".")[-1].replace("_", " ").title()
        return "📢", label
    if event_type and event_type != "*":
        return "📢", event_type.replace("_", " ").title()
    return "📢", "Alert"


def _detail_url(attributes: dict[str, Any], body: str) -> str:
    url = attributes.get("url")
    if isinstance(url, str) and url.startswith(("http://", "https://")):
        return url.strip()

    match = _URL_RE.search(body)
    if match:
        return match.group(0).rstrip(").,]")
    return ""


def _summary_without_url(body: str, attributes: dict[str, Any]) -> str:
    detail_url = _detail_url(attributes, body)
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


def _normalize_attributes(raw: Any) -> dict[str, Any]:
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


def _format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)
    return str(value)


def _humanize_key(key: str) -> str:
    return key.replace("_", " ").strip().title()


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
