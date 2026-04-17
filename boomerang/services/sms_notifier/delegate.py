import asyncio
import json
import urllib.error
import urllib.request

from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang.core.contracts.notification import NotificationRequest
from boomerang.services.sms_notifier.database import Database
from boomerang.services.sms_notifier.exceptions import NotFoundError, ValidationError
from boomerang.services.sms_notifier.http_models import CreateSmsEndpointRequest


class SmsNotifierDelegate(ServiceDelegate):
    async def setup(self) -> None:
        config = self.container.config
        sqlite_path = get_parameter(
            config, "app.storage.sqlite_path", "/data/sms_notifier.sqlite3"
        )
        self._database = Database(sqlite_path)
        self._database.setup()

        # Provider configuration reserved for upcoming delivery implementation.
        self._provider_base_url = get_parameter(config, "app.sms.provider.base_url", "")
        self._provider_api_key = get_parameter(config, "app.sms.provider.api_key", "")
        self._provider_sender_id = get_parameter(
            config, "app.sms.provider.sender_id", ""
        )

    async def create_sms_endpoint(
        self, user_id: str, model: CreateSmsEndpointRequest
    ) -> dict:
        if not isinstance(model, CreateSmsEndpointRequest):
            raise ValidationError("Invalid request payload.")

        record = self._database.upsert_sms_endpoint(
            user_id=user_id,
            endpoint_key=model.endpoint_key,
            phone_number=model.phone_number,
        )
        return {
            "status": "ok",
            "endpoint": {
                "user_id": record["user_id"],
                "endpoint_key": record["endpoint_key"],
                "phone_number": record["phone_number"],
            },
        }

    async def list_sms_endpoints(self, user_id: str) -> dict:
        endpoints = self._database.list_sms_endpoints(user_id)
        return {
            "status": "ok",
            "endpoints": [
                {
                    "user_id": e["user_id"],
                    "endpoint_key": e["endpoint_key"],
                    "phone_number": e["phone_number"],
                }
                for e in endpoints
            ],
        }

    async def get_sms_endpoint(self, user_id: str, endpoint_key: str) -> dict:
        key = (endpoint_key or "").strip()
        if not key:
            raise ValidationError("Invalid request payload.")
        endpoint = self._database.get_sms_endpoint(user_id, key)
        if endpoint is None:
            raise NotFoundError("Resource not found.")
        return {
            "status": "ok",
            "endpoint": {
                "user_id": endpoint["user_id"],
                "endpoint_key": endpoint["endpoint_key"],
                "phone_number": endpoint["phone_number"],
            },
        }

    async def delete_sms_endpoint(self, user_id: str, endpoint_key: str) -> dict:
        key = (endpoint_key or "").strip()
        if not key:
            raise ValidationError("Invalid request payload.")
        deleted = self._database.delete_sms_endpoint(user_id, key)
        if not deleted:
            raise NotFoundError("Resource not found.")
        return {"status": "ok"}

    async def send_notification_sms(self, request: NotificationRequest) -> None:
        if request.channel != "sms":
            return
        destination_kind = request.destination.kind.strip().lower()
        if destination_kind != "phone_number":
            raise ValidationError("Invalid request payload.")
        await asyncio.to_thread(
            self._send_via_http_provider,
            to=request.destination.value,
            body=request.message.body,
            sender_id=self._provider_sender_id,
            title=request.message.title,
        )

    def _send_via_http_provider(
        self, *, to: str, body: str, sender_id: str, title: str
    ) -> None:
        payload = json.dumps(
            {"to": to, "body": body, "sender_id": sender_id, "title": title}
        ).encode("utf-8")
        request = urllib.request.Request(
            url=f"{self._provider_base_url.rstrip('/')}/sms/send",
            method="POST",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._provider_api_key}",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=10):
                return
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"sms provider error: {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"sms provider unreachable: {exc.reason}") from exc

