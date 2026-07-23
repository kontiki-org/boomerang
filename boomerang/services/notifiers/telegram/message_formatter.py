import re
from typing import Any

from boomerang_contracts.notification.message import NotificationMessage

_URL_RE = re.compile(r"https?://[^\s]+")

_SEVERITY_ICONS: dict[str, str] = {
    "low": "🟢",
    "moderate": "🟡",
    "severe": "🟠",
    "critical": "🔴",
    "unknown": "⚪",
}


def normalize_category_icons(raw: Any) -> dict[str, str]:
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


def format_telegram_notification(
    message: NotificationMessage,
    category_icons: dict[str, str] | None = None,
) -> tuple[str, str | None]:
    title = message.title.strip()
    body = message.body.strip()
    context = message.context
    data = context.data if context is not None else {}
    icons = category_icons if category_icons is not None else {}

    category = _as_text(data.get("category")).lower()
    if category or (context is not None and context.kind.strip().lower() == "alert"):
        return _format_structured_alert(
            title=title,
            body=body,
            category=category,
            event_type=_as_text(data.get("event_type")).lower(),
            severity=_as_text(data.get("severity")).lower() or "unknown",
            attributes=_normalize_attributes(data.get("attributes")),
            category_icons=icons,
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
    category_icons: dict[str, str],
) -> tuple[str, str | None]:
    category_icon = _resolve_category_icon(category, category_icons)
    banner_label = _resolve_banner_label(category, event_type)
    severity_icon = _SEVERITY_ICONS.get(severity, _SEVERITY_ICONS["unknown"])

    banner_parts = [part for part in (category_icon, severity_icon) if part]
    banner_parts.append(f"<b>{_escape_html(banner_label)}</b>")
    lines = [" ".join(banner_parts), ""]

    metadata_lines = _metadata_lines(attributes)
    if metadata_lines:
        lines.extend(metadata_lines)
        lines.append("")
    elif title:
        lines.append(_escape_html(title))
        lines.append("")

    # Always surface body when it adds information (not only when attributes
    # are empty — otherwise exception messages and similar text are dropped).
    summary = _summary_without_url(body, attributes)
    if summary and summary != title:
        lines.append(
            f"<b>{_escape_html('Message')}:</b> {_escape_html(_format_value(summary))}"
        )
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
    for key, value in attributes.items():
        if key == "url" or value is None or value == "":
            continue
        label = _humanize_key(key)
        lines.append(
            f"<b>{_escape_html(label)}:</b> {_escape_html(_format_value(value))}"
        )
    return lines


def _resolve_category_icon(category: str, category_icons: dict[str, str]) -> str:
    if not category or not category_icons:
        return ""
    if category in category_icons:
        return category_icons[category]

    for prefix, icon in category_icons.items():
        if category.startswith(f"{prefix}.") or category.startswith(prefix):
            return icon
    return ""


def _resolve_banner_label(category: str, event_type: str) -> str:
    # Prefer alert type (event_type); fall back to last category segment.
    if event_type and event_type != "*":
        return _humanize_key(event_type)
    if category:
        return _humanize_key(category.split(".")[-1])
    return "Alert"


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
