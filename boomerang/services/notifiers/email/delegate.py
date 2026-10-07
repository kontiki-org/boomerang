import asyncio
import smtplib
from email.message import EmailMessage

from boomerang_contracts.notification.channel_catalog import NotificationChannelCatalog
from boomerang_contracts.notification.message import NotificationRequest
from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang.core.exceptions import ValidationError
from boomerang.services.notifiers.email.channel_catalog import (
    email_notification_channel_catalog,
)
from boomerang.services.notifiers.email.configured_endpoints import (
    load_configured_endpoints,
)
from boomerang.services.notifiers.email.message_formatter import (
    format_email_notification,
)


class EmailNotifierDelegate(ServiceDelegate):
    async def setup(self) -> None:
        config = self.container.config
        self._channel_catalog = email_notification_channel_catalog()
        self.channel_id = self._channel_catalog.channel_id
        configured_endpoints = get_parameter(config, "app.endpoints", None)
        self.configured_endpoints = load_configured_endpoints(
            configured_endpoints,
            self._channel_catalog,
        )

        self._smtp_host = get_parameter(config, "app.email.smtp.host", "localhost")
        self._smtp_port = int(get_parameter(config, "app.email.smtp.port", 25))
        self._smtp_use_starttls = bool(
            get_parameter(config, "app.email.smtp.use_starttls", True)
        )
        self._smtp_username = get_parameter(config, "app.email.smtp.username", "")
        self._smtp_password = get_parameter(config, "app.email.smtp.password", "")
        self._from_address = get_parameter(
            config, "app.email.from.address", "no-reply@example.org"
        )
        self._degraded_after_failures = int(
            get_parameter(config, "app.email.degraded_after_failures", 3)
        )
        self._consecutive_smtp_failures = 0

    async def get_notification_channel_catalog(self) -> NotificationChannelCatalog:
        return self._channel_catalog

    async def send_notification(self, request: NotificationRequest) -> None:
        destination_value = self._resolve_destination_address(request)
        subject, plain_body, html_body = format_email_notification(request.message)
        from_address = (self._from_address or "").strip()

        try:
            await asyncio.to_thread(
                self._send_via_smtp,
                from_address=from_address,
                to_address=destination_value,
                subject=subject,
                plain_body=plain_body,
                html_body=html_body,
            )
        except Exception:
            self._consecutive_smtp_failures += 1
            raise
        self._consecutive_smtp_failures = 0

    def is_degraded_due_to_smtp_failures(self) -> bool:
        threshold = max(1, self._degraded_after_failures)
        return self._consecutive_smtp_failures >= threshold

    def _resolve_destination_address(self, request: NotificationRequest) -> str:
        endpoint_key = (request.endpoint_key or "").strip()
        if not endpoint_key:
            raise ValidationError()

        configured = self.configured_endpoints.get(endpoint_key)
        if configured is None:
            raise ValidationError()

        address = (configured.get("address") or "").strip().lower()
        if not address:
            raise ValidationError()
        return address

    def _send_via_smtp(
        self,
        *,
        from_address: str,
        to_address: str,
        subject: str,
        plain_body: str,
        html_body: str,
    ) -> None:
        message = EmailMessage()
        message["From"] = from_address
        message["To"] = to_address
        message["Subject"] = subject
        message.set_content(plain_body or "")
        if html_body:
            message.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(self._smtp_host, self._smtp_port, timeout=10) as smtp:
            if self._smtp_use_starttls:
                smtp.starttls()
            if self._smtp_username:
                smtp.login(self._smtp_username, self._smtp_password)
            smtp.send_message(message)
