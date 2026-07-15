import asyncio
import json
import re
import urllib.error
import urllib.request

from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang.core.contracts.notification import NotificationRequest
from boomerang.core.contracts.notification_channel_catalog import (
    NotificationChannelCatalog,
)
from boomerang.core.contracts.notification_endpoint import CreateEndpointRequest
from boomerang.core.exceptions import NotFoundError, ValidationError
from boomerang.core.notification_channel_validation import (
    endpoint_display,
    validate_endpoint_fields,
)
from boomerang.services.telegram_notifier.channel_catalog import (
    telegram_notification_channel_catalog,
)
from boomerang.services.telegram_notifier.database import Database
from boomerang.services.telegram_notifier.message_formatter import (
    format_telegram_notification,
)


class TelegramNotifierDelegate(ServiceDelegate):
    async def setup(self) -> None:
        config = self.container.config
        sqlite_path = get_parameter(
            config, "app.storage.sqlite_path", "/data/telegram_notifier.sqlite3"
        )
        self._database = Database(sqlite_path)
        self._database.setup()
        self._channel_catalog = telegram_notification_channel_catalog()

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

    async def create_endpoint(self, user_id: str, model: CreateEndpointRequest) -> dict:
        if not isinstance(model, CreateEndpointRequest):
            model = CreateEndpointRequest.model_validate(model)

        fields = validate_endpoint_fields(self._channel_catalog, model.fields)
        chat_id = fields["chat_id"]
        if not re.fullmatch(r"-?\d+", chat_id):
            raise ValidationError()
        record = self._database.upsert_telegram_endpoint(
            user_id=user_id,
            endpoint_key=model.endpoint_key,
            chat_id=chat_id,
        )
        return {"endpoint": self._endpoint_payload(record, fields)}

    async def list_endpoints(self, user_id: str) -> dict:
        endpoints = self._database.list_telegram_endpoints(user_id)
        return {
            "endpoints": [
                self._endpoint_payload(
                    endpoint,
                    {"chat_id": endpoint["chat_id"]},
                )
                for endpoint in endpoints
            ],
        }

    async def get_endpoint(self, user_id: str, endpoint_key: str) -> dict:
        key = (endpoint_key or "").strip()
        if not key:
            raise ValidationError()
        endpoint = self._database.get_telegram_endpoint(user_id, key)
        if endpoint is None:
            raise NotFoundError()
        return {
            "endpoint": self._endpoint_payload(
                endpoint,
                {"chat_id": endpoint["chat_id"]},
            ),
        }

    async def delete_endpoint(self, user_id: str, endpoint_key: str) -> dict:
        key = (endpoint_key or "").strip()
        if not key:
            raise ValidationError()
        deleted = self._database.delete_telegram_endpoint(user_id, key)
        if not deleted:
            raise NotFoundError()
        return {}

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

    def _endpoint_payload(self, record: dict, fields: dict[str, str]) -> dict:
        return {
            "user_id": record["user_id"],
            "endpoint_key": record["endpoint_key"],
            "fields": fields,
            "display": endpoint_display(self._channel_catalog, fields),
        }

    def _resolve_chat_id(self, request: NotificationRequest) -> str:
        user_id = (request.recipient_id or "").strip()
        endpoint_key = (request.endpoint_key or "").strip()
        if not user_id or not endpoint_key:
            raise ValidationError()

        endpoint = self._database.get_telegram_endpoint(user_id, endpoint_key)
        if endpoint is None:
            raise ValidationError()

        chat_id = (endpoint.get("chat_id") or "").strip()
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
