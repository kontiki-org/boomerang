import asyncio
import json
import urllib.error
import urllib.request

from boomerang_contracts.notification.message import NotificationRequest
from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang.core.exceptions import ValidationError
from boomerang.services.notifiers.ntfy.channel_catalog import (
    ntfy_notification_channel_catalog,
)
from boomerang.services.notifiers.ntfy.configured_endpoints import (
    load_configured_endpoints,
)
from boomerang.services.notifiers.ntfy.message_formatter import (
    format_ntfy_notification,
    normalize_category_icons,
)


class NtfyNotifierDelegate(ServiceDelegate):
    async def setup(self):
        config = self.container.config
        self._channel_catalog = ntfy_notification_channel_catalog()
        self.channel_id = self._channel_catalog.channel_id
        configured_endpoints = get_parameter(config, "app.endpoints", None)
        self.configured_endpoints = load_configured_endpoints(
            configured_endpoints,
            self._channel_catalog,
        )

        self._token = get_parameter(config, "app.ntfy.token", "")
        self._server_url = get_parameter(
            config, "app.ntfy.server_url", "https://ntfy.sh"
        )
        self._degraded_after_failures = int(
            get_parameter(config, "app.ntfy.degraded_after_failures", 3)
        )
        self._category_icons = normalize_category_icons(
            get_parameter(config, "app.ntfy.category_icons", None)
        )
        self._consecutive_api_failures = 0

    async def get_notification_channel_catalog(self):
        return self._channel_catalog

    async def send_notification(self, request: NotificationRequest):
        topic = self._resolve_topic(request)
        payload = format_ntfy_notification(
            request.message,
            category_icons=self._category_icons,
        )

        try:
            await asyncio.to_thread(
                self._send_via_ntfy,
                topic=topic,
                payload=payload,
            )
        except Exception:
            self._consecutive_api_failures += 1
            raise
        self._consecutive_api_failures = 0

    def is_degraded_due_to_api_failures(self):
        threshold = max(1, self._degraded_after_failures)
        return self._consecutive_api_failures >= threshold

    def _resolve_topic(self, request):
        endpoint_key = (request.endpoint_key or "").strip()
        if not endpoint_key:
            raise ValidationError()

        configured = self.configured_endpoints.get(endpoint_key)
        if configured is None:
            raise ValidationError()

        topic = (configured.get("topic") or "").strip()
        if not topic:
            raise ValidationError()
        return topic

    def _send_via_ntfy(self, *, topic, payload):
        body = {"topic": topic, **payload}
        data = json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        token = (self._token or "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(
            url=f"{self._server_url.rstrip('/')}/",
            method="POST",
            data=data,
            headers=headers,
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                response.read()
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"ntfy api error: {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"ntfy api unreachable: {exc.reason}") from exc
