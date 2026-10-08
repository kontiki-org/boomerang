from boomerang.services.notifiers.common.structured_alert import (
    normalize_category_icons,
    parse_structured_alert,
    resolve_category_icon,
)

_SEVERITY_PRIORITY = {
    "low": 2,
    "moderate": 3,
    "severe": 4,
    "critical": 5,
}


def format_ntfy_notification(message, category_icons=None):
    icons = category_icons if category_icons is not None else {}
    parts = parse_structured_alert(message)
    if parts is not None:
        return _format_structured(parts, icons)
    return _format_plain(message)


def _format_plain(message):
    title = message.title.strip()
    body = message.body.strip()
    if title and body and title != body:
        text_title = title
        text_message = body
    else:
        text = title or body
        text_title = text
        text_message = text
    return {
        "title": text_title,
        "message": text_message,
        "markdown": False,
        "priority": 3,
    }


def _format_structured(parts, category_icons):
    message = _format_markdown(parts) or parts.banner_label
    payload = {
        "title": parts.banner_label,
        "message": message,
        "markdown": True,
        "priority": _SEVERITY_PRIORITY.get(parts.severity, 3),
    }
    icon = resolve_category_icon(parts.category, category_icons)
    if icon:
        payload["tags"] = [icon]
    if parts.detail_url:
        payload["click"] = parts.detail_url
    return payload


def _format_markdown(parts):
    lines = []
    if parts.attributes:
        for label, value in parts.attributes:
            lines.append(f"**{label}:** {value}")
        lines.append("")
    elif parts.title:
        lines.append(parts.title)
        lines.append("")
    if parts.message:
        lines.append(f"**Message:** {parts.message}")
        lines.append("")
    return "\n".join(lines).strip()


__all__ = ["format_ntfy_notification", "normalize_category_icons"]
