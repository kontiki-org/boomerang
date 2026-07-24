from boomerang_contracts.notification.message import NotificationMessage

from boomerang.services.notifiers.common.structured_alert import (
    SEVERITY_ICONS,
    escape_html,
    normalize_category_icons,
    parse_structured_alert,
    resolve_category_icon,
)


def format_telegram_notification(
    message: NotificationMessage,
    category_icons: dict[str, str] | None = None,
) -> tuple[str, str | None]:
    icons = category_icons if category_icons is not None else {}
    parts = parse_structured_alert(message)
    if parts is not None:
        return _format_structured_html(parts, icons), "HTML"

    title = message.title.strip()
    body = message.body.strip()
    if title and body:
        return f"{title}\n\n{body}", None
    return title or body, None


def _format_structured_html(parts, category_icons: dict[str, str]) -> str:
    category_icon = resolve_category_icon(parts.category, category_icons)
    severity_icon = SEVERITY_ICONS.get(parts.severity, SEVERITY_ICONS["unknown"])

    banner_parts = [part for part in (category_icon, severity_icon) if part]
    banner_parts.append(f"<b>{escape_html(parts.banner_label)}</b>")
    lines = [" ".join(banner_parts), ""]

    if parts.attributes:
        for label, value in parts.attributes:
            lines.append(f"<b>{escape_html(label)}:</b> {escape_html(value)}")
        lines.append("")
    elif parts.title:
        lines.append(escape_html(parts.title))
        lines.append("")

    if parts.message:
        lines.append(f"<b>{escape_html('Message')}:</b> {escape_html(parts.message)}")
        lines.append("")

    if parts.detail_url:
        safe_url = escape_html(parts.detail_url)
        lines.append(f'🔗 <a href="{safe_url}">Details</a>')

    return "\n".join(line for line in lines if line is not None).strip()


# Re-export for callers that imported normalize from this module.
__all__ = ["format_telegram_notification", "normalize_category_icons"]
