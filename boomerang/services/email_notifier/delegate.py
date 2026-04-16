from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang.services.email_notifier.database import Database
from boomerang.services.email_notifier.exceptions import ValidationError
from boomerang.services.email_notifier.http_models import CreateEmailEndpointRequest


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
            raise ValidationError("Invalid request payload.")

        record = self._database.upsert_email_endpoint(
            user_id=user_id,
            endpoint_key=model.endpoint_key,
            address=model.address,
        )
        return {
            "status": "ok",
            "endpoint": {
                "user_id": record["user_id"],
                "endpoint_key": record["endpoint_key"],
                "address": record["address"],
            },
        }
