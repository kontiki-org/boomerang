from boomerang.services.notifiers.common.structured_alert import (
    SEVERITY_ICONS,
    normalize_category_icons,
    parse_structured_alert,
    resolve_category_icon,
)


def format_zulip_notification(message, category_icons=None):
    icons = category_icons if category_icons is not None else {}
    parts = parse_structured_alert(message)
    if parts is not None:
        return _format_structured(parts, icons)
    title = message.title.strip()
    body = message.body.strip()
    if title and body:
        return f"{title}\n\n{body}"
    return title or body


def _format_structured(parts, category_icons):
    category_icon = resolve_category_icon(parts.category, category_icons)
    severity_icon = SEVERITY_ICONS.get(parts.severity, SEVERITY_ICONS["unknown"])
    banner_parts = [part for part in (category_icon, severity_icon) if part]
    banner_parts.append(f"**{parts.banner_label}**")
    lines = [" ".join(banner_parts), ""]

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

    if parts.detail_url:
        lines.append(f"🔗 [Details]({parts.detail_url})")

    return "\n".join(line for line in lines if line is not None).strip()


__all__ = ["format_zulip_notification", "normalize_category_icons"]
