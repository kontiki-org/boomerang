import asyncio
import base64
import json
import urllib.error
import urllib.request

from boomerang_contracts.notification.message import NotificationRequest
from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang.core.exceptions import ValidationError
from boomerang.services.notifiers.zulip.channel_catalog import (
    zulip_notification_channel_catalog,
)
from boomerang.services.notifiers.zulip.configured_endpoints import (
    load_configured_endpoints,
)
from boomerang.services.notifiers.zulip.message_formatter import (
    format_zulip_notification,
    normalize_category_icons,
)


class ZulipNotifierDelegate(ServiceDelegate):
    async def setup(self):
        config = self.container.config
        self._channel_catalog = zulip_notification_channel_catalog()
        self.channel_id = self._channel_catalog.channel_id
        configured_endpoints = get_parameter(config, "app.endpoints", None)
        self.configured_endpoints = load_configured_endpoints(
            configured_endpoints,
            self._channel_catalog,
        )

        self._api_key = get_parameter(config, "app.zulip.api_key", "")
        self._bot_email = get_parameter(config, "app.zulip.bot_email", "")
        self._site_url = get_parameter(config, "app.zulip.site_url", "")
        self._degraded_after_failures = int(
            get_parameter(config, "app.zulip.degraded_after_failures", 3)
        )
        self._category_icons = normalize_category_icons(
            get_parameter(config, "app.zulip.category_icons", None)
        )
        self._consecutive_api_failures = 0

    async def get_notification_channel_catalog(self):
        return self._channel_catalog

    async def send_notification(self, request: NotificationRequest):
        channel, topic = self._resolve_destination(request)
        content = format_zulip_notification(
            request.message,
            category_icons=self._category_icons,
        )

        try:
            await asyncio.to_thread(
                self._send_via_zulip,
                channel=channel,
                topic=topic,
                content=content,
            )
        except Exception:
            self._consecutive_api_failures += 1
            raise
        self._consecutive_api_failures = 0

    def is_degraded_due_to_api_failures(self):
        threshold = max(1, self._degraded_after_failures)
        return self._consecutive_api_failures >= threshold

    def _resolve_destination(self, request):
        endpoint_key = (request.endpoint_key or "").strip()
        if not endpoint_key:
            raise ValidationError()

        configured = self.configured_endpoints.get(endpoint_key)
        if configured is None:
            raise ValidationError()

        channel = (configured.get("channel") or "").strip()
        topic = (configured.get("topic") or "").strip()
        if not channel or not topic:
            raise ValidationError()
        return channel, topic

    def _send_via_zulip(self, *, channel, topic, content):
        email = (self._bot_email or "").strip()
        api_key = (self._api_key or "").strip()
        site_url = (self._site_url or "").strip()
        if not email or not api_key:
            raise RuntimeError("zulip bot credentials are not configured")
        if not site_url:
            raise RuntimeError("zulip site url is not configured")

        token = base64.b64encode(f"{email}:{api_key}".encode("utf-8")).decode("ascii")
        payload = json.dumps(
            {
                "type": "stream",
                "to": channel,
                "topic": topic,
                "content": content,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            url=f"{site_url.rstrip('/')}/api/v1/messages",
            method="POST",
            data=payload,
            headers={
                "Authorization": f"Basic {token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"zulip api error: {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"zulip api unreachable: {exc.reason}") from exc

        if not isinstance(body, dict) or body.get("result") != "success":
            raise RuntimeError("zulip api returned an error response")
