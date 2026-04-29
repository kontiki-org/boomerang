import asyncio
import logging
import smtplib
from email.message import EmailMessage

from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang.core.contracts.email_notifier import CreateEmailEndpointRequest
from boomerang.core.contracts.notification import NotificationRequest
from boomerang.core.exceptions import NotFoundError, ValidationError
from boomerang.services.email_notifier.database import Database


class EmailNotifierDelegate(ServiceDelegate):
    async def setup(self) -> None:
        config = self.container.config
        sqlite_path = get_parameter(
            config, "app.storage.sqlite_path", "/data/email_notifier.sqlite3"
        )
        self._database = Database(sqlite_path)
        self._database.setup()

        # SMTP configuration (read-only for now, sending not yet implemented).
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

    async def create_email_endpoint(
        self, user_id: str, model: CreateEmailEndpointRequest
    ) -> dict:
        if not isinstance(model, CreateEmailEndpointRequest):
            raise ValidationError()

        record = self._database.upsert_email_endpoint(
            user_id=user_id,
            endpoint_key=model.endpoint_key,
            address=model.address,
        )
        return {
            "endpoint": {
                "user_id": record["user_id"],
                "endpoint_key": record["endpoint_key"],
                "address": record["address"],
            },
        }

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

    async def list_email_endpoints(self, user_id: str) -> dict:
        endpoints = self._database.list_email_endpoints(user_id)
        return {
            "endpoints": [
                {
                    "user_id": e["user_id"],
                    "endpoint_key": e["endpoint_key"],
                    "address": e["address"],
                }
                for e in endpoints
            ],
        }

    async def get_email_endpoint(self, user_id: str, endpoint_key: str) -> dict:
        key = (endpoint_key or "").strip()
        if not key:
            raise ValidationError()
        endpoint = self._database.get_email_endpoint(user_id, key)
        if endpoint is None:
            raise NotFoundError()
        return {
            "endpoint": {
                "user_id": endpoint["user_id"],
                "endpoint_key": endpoint["endpoint_key"],
                "address": endpoint["address"],
            },
        }

    async def delete_email_endpoint(self, user_id: str, endpoint_key: str) -> dict:
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

        await asyncio.to_thread(
            self._send_via_smtp,
            from_address=from_address,
            to_address=destination_value,
            subject=subject,
            body=body,
        )

    def _resolve_destination_address(self, request: NotificationRequest) -> str:
        user_id = (request.recipient_id or "").strip()
        endpoint_key = (request.endpoint_key or "").strip()
        if not user_id or not endpoint_key:
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
