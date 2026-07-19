import asyncio
import json
import urllib.error
import urllib.request

from boomerang_contracts.notification.channel_catalog import NotificationChannelCatalog
from boomerang_contracts.notification.message import NotificationRequest
from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang.core.exceptions import ValidationError
from boomerang.services.notifiers.telegram.channel_catalog import (
    telegram_notification_channel_catalog,
)
from boomerang.services.notifiers.telegram.configured_endpoints import (
    load_configured_endpoints,
)
from boomerang.services.notifiers.telegram.message_formatter import (
    format_telegram_notification,
)


class TelegramNotifierDelegate(ServiceDelegate):
    async def setup(self) -> None:
        config = self.container.config
        self._channel_catalog = telegram_notification_channel_catalog()
        configured_endpoints = get_parameter(config, "app.endpoints", None)
        self._configured_endpoints = load_configured_endpoints(
            configured_endpoints,
            self._channel_catalog,
        )

        self._bot_token = get_parameter(config, "app.telegram.bot_token", "")
        self._api_base_url = get_parameter(
            config, "app.telegram.api_base_url", "https://api.telegram.org"
        )
        self._degraded_after_failures = int(
            get_parameter(config, "app.telegram.degraded_after_failures", 3)
        )
        self._consecutive_api_failures = 0

    async def get_notification_channel_catalog(self) -> NotificationChannelCatalog:
        return self._channel_catalog

    async def send_notification_telegram(self, request: NotificationRequest) -> None:
        chat_id = self._resolve_chat_id(request)
        text, parse_mode = format_telegram_notification(request.message)

        try:
            await asyncio.to_thread(
                self._send_via_telegram_api,
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
            )
        except Exception:
            self._consecutive_api_failures += 1
            raise
        self._consecutive_api_failures = 0

    def is_degraded_due_to_api_failures(self) -> bool:
        threshold = max(1, self._degraded_after_failures)
        return self._consecutive_api_failures >= threshold

    def _resolve_chat_id(self, request: NotificationRequest) -> str:
        endpoint_key = (request.endpoint_key or "").strip()
        if not endpoint_key:
            raise ValidationError()

        configured = self._configured_endpoints.get(endpoint_key)
        if configured is None:
            raise ValidationError()

        chat_id = (configured.get("chat_id") or "").strip()
        if not chat_id:
            raise ValidationError()
        return chat_id

    def _send_via_telegram_api(
        self, *, chat_id: str, text: str, parse_mode: str | None = None
    ) -> None:
        token = (self._bot_token or "").strip()
        if not token:
            raise RuntimeError("telegram bot token is not configured")

        payload_data = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload_data["parse_mode"] = parse_mode
        payload = json.dumps(payload_data).encode("utf-8")
        request = urllib.request.Request(
            url=f"{self._api_base_url.rstrip('/')}/bot{token}/sendMessage",
            method="POST",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"telegram api error: {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"telegram api unreachable: {exc.reason}") from exc

        if not isinstance(body, dict) or not body.get("ok"):
            raise RuntimeError("telegram api returned an error response")
