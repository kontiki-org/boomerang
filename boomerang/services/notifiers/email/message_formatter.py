from boomerang_contracts.notification.message import NotificationMessage

from boomerang.services.notifiers.common.structured_alert import (
    SEVERITY_ICONS,
    escape_html,
    parse_structured_alert,
)


def format_email_notification(message: NotificationMessage):
    """Return (subject, plain_body, html_body)."""
    parts = parse_structured_alert(message)
    if parts is not None:
        return (
            parts.banner_label,
            _format_structured_plain(parts),
            _format_structured_html(parts),
        )

    title = message.title.strip()
    body = message.body.strip()
    if title and body and title != body:
        plain = f"{title}\n\n{body}"
        html = f"<p><b>{escape_html(title)}</b></p>" f"<p>{escape_html(body)}</p>"
        return title, plain, html
    text = title or body
    return text, text, f"<p>{escape_html(text)}</p>" if text else ""


def _format_structured_plain(parts):
    lines = [parts.banner_label, ""]
    if parts.attributes:
        for label, value in parts.attributes:
            lines.append(f"{label}: {value}")
        lines.append("")
    elif parts.title:
        lines.append(parts.title)
        lines.append("")
    if parts.message:
        lines.append(f"Message: {parts.message}")
        lines.append("")
    if parts.detail_url:
        lines.append(f"Details: {parts.detail_url}")
    return "\n".join(lines).strip()


def _format_structured_html(parts):
    severity_icon = SEVERITY_ICONS.get(parts.severity, SEVERITY_ICONS["unknown"])
    lines = [
        f"<p>{severity_icon} <b>{escape_html(parts.banner_label)}</b></p>",
    ]

    if parts.attributes:
        rows = []
        for label, value in parts.attributes:
            rows.append(f"<li><b>{escape_html(label)}:</b> {escape_html(value)}</li>")
        lines.append("<ul>" + "".join(rows) + "</ul>")
    elif parts.title:
        lines.append(f"<p>{escape_html(parts.title)}</p>")

    if parts.message:
        lines.append(
            f"<p><b>{escape_html('Message')}:</b> " f"{escape_html(parts.message)}</p>"
        )

    if parts.detail_url:
        safe_url = escape_html(parts.detail_url)
        lines.append(f'<p><a href="{safe_url}">Details</a></p>')

    return "\n".join(lines)
