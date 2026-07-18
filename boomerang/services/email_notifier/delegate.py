import asyncio
import logging
import smtplib
from email.message import EmailMessage

from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang_contracts.notification.message import NotificationRequest
from boomerang_contracts.notification.channel_catalog import (
    NotificationChannelCatalog,
)
from boomerang_contracts.notification.endpoint import CreateEndpointRequest
from boomerang.core.exceptions import NotFoundError, ValidationError
from boomerang_contracts.notification.validation import (
    endpoint_display,
    validate_endpoint_fields,
)
from boomerang.services.email_notifier.channel_catalog import (
    email_notification_channel_catalog,
)
from boomerang.services.email_notifier.configured_endpoints import (
    load_configured_endpoints,
)
from boomerang.services.email_notifier.database import Database


class EmailNotifierDelegate(ServiceDelegate):
    async def setup(self) -> None:
        config = self.container.config
        sqlite_path = get_parameter(
            config, "app.storage.sqlite_path", "/data/email_notifier.sqlite3"
        )
        self._database = Database(sqlite_path)
        self._database.setup()
        self._channel_catalog = email_notification_channel_catalog()
        configured_endpoints = get_parameter(config, "app.endpoints", None)
        self._configured_endpoints = load_configured_endpoints(
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

    async def create_endpoint(self, user_id: str, model: CreateEndpointRequest) -> dict:
        if not isinstance(model, CreateEndpointRequest):
            model = CreateEndpointRequest.model_validate(model)

        fields = validate_endpoint_fields(self._channel_catalog, model.fields)
        address = fields["address"]
        record = self._database.upsert_email_endpoint(
            user_id=user_id,
            endpoint_key=model.endpoint_key,
            address=address,
        )
        return {"endpoint": self._endpoint_payload(record, fields)}

    async def ensure_auth_email_endpoint(
        self,
        user_id: str,
        endpoint_key: str,
        address: str,
    ) -> dict:
        endpoint = self._database.get_email_endpoint(user_id, endpoint_key)
        if endpoint is not None:
            logging.info(
                "ensure_auth_email_endpoint: endpoint already exists for user_id=%s endpoint_key=%s",
                user_id,
                endpoint_key,
            )
            return {
                "endpoint": {
                    "user_id": endpoint["user_id"],
                    "endpoint_key": endpoint["endpoint_key"],
                    "address": endpoint["address"],
                },
            }

        record = self._database.upsert_email_endpoint(
            user_id=user_id,
            endpoint_key=endpoint_key,
            address=address,
        )
        return {
            "endpoint": {
                "user_id": record["user_id"],
                "endpoint_key": record["endpoint_key"],
                "address": record["address"],
            },
        }

    async def list_endpoints(self, user_id: str) -> dict:
        endpoints = self._database.list_email_endpoints(user_id)
        return {
            "endpoints": [
                self._endpoint_payload(
                    endpoint,
                    {"address": endpoint["address"]},
                )
                for endpoint in endpoints
            ],
        }

    async def get_endpoint(self, user_id: str, endpoint_key: str) -> dict:
        key = (endpoint_key or "").strip()
        if not key:
            raise ValidationError()
        endpoint = self._database.get_email_endpoint(user_id, key)
        if endpoint is None:
            raise NotFoundError()
        return {
            "endpoint": self._endpoint_payload(
                endpoint,
                {"address": endpoint["address"]},
            ),
        }

    async def delete_endpoint(self, user_id: str, endpoint_key: str) -> dict:
        key = (endpoint_key or "").strip()
        if not key:
            raise ValidationError()
        deleted = self._database.delete_email_endpoint(user_id, key)
        if not deleted:
            raise NotFoundError()
        return {}

    async def send_notification_email(self, request: NotificationRequest) -> None:
        destination_value = self._resolve_destination_address(request)
        subject = request.message.title.strip()
        body = request.message.body.strip()
        from_address = (self._from_address or "").strip()

        try:
            await asyncio.to_thread(
                self._send_via_smtp,
                from_address=from_address,
                to_address=destination_value,
                subject=subject,
                body=body,
            )
        except Exception:
            self._consecutive_smtp_failures += 1
            raise
        self._consecutive_smtp_failures = 0

    def is_degraded_due_to_smtp_failures(self) -> bool:
        threshold = max(1, self._degraded_after_failures)
        return self._consecutive_smtp_failures >= threshold

    def _endpoint_payload(self, record: dict, fields: dict[str, str]) -> dict:
        return {
            "user_id": record["user_id"],
            "endpoint_key": record["endpoint_key"],
            "fields": fields,
            "display": endpoint_display(self._channel_catalog, fields),
        }

    def _resolve_destination_address(self, request: NotificationRequest) -> str:
        endpoint_key = (request.endpoint_key or "").strip()
        if not endpoint_key:
            raise ValidationError()

        configured = self._configured_endpoints.get(endpoint_key)
        if configured is not None:
            address = (configured.get("address") or "").strip().lower()
            if not address:
                raise ValidationError()
            return address

        user_id = (request.recipient_id or "").strip()
        if not user_id:
            raise ValidationError()

        endpoint = self._database.get_email_endpoint(user_id, endpoint_key)
        if endpoint is None:
            raise ValidationError()

        address = (endpoint.get("address") or "").strip().lower()
        if not address:
            raise ValidationError()
        return address

    def _send_via_smtp(
        self,
        *,
        from_address: str,
        to_address: str,
        subject: str,
        body: str,
    ) -> None:
        message = EmailMessage()
        message["From"] = from_address
        message["To"] = to_address
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(self._smtp_host, self._smtp_port, timeout=10) as smtp:
            if self._smtp_use_starttls:
                smtp.starttls()
            if self._smtp_username:
                smtp.login(self._smtp_username, self._smtp_password)
            smtp.send_message(message)
