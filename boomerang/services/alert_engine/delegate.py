import secrets

from boomerang_contracts.alert.normalized import NormalizedAlert
from boomerang_contracts.notification.message import (
    NotificationContext,
    NotificationMessage,
    NotificationRequest,
)
from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate
from pydantic import ValidationError as PydanticValidationError

from boomerang.core.exceptions import AuthError, ValidationError
from boomerang.core.service_contracts.subscription.service import SubscriptionRpcProxy


class AlertEngineDelegate(ServiceDelegate):
    async def setup(self):
        config = self.container.config
        token = get_parameter(config, "app.http.token", "")
        self._http_token = token if isinstance(token, str) else ""

    def require_http_auth(self, request):
        expected = self._http_token
        if not expected:
            raise AuthError()
        auth_header = request.headers.get("Authorization") or request.headers.get(
            "authorization"
        )
        if not isinstance(auth_header, str) or not auth_header.startswith("Bearer "):
            raise AuthError()
        provided = auth_header[len("Bearer ") :]
        if not secrets.compare_digest(provided, expected):
            raise AuthError()

    async def parse_normalized_alert(self, request):
        try:
            payload = await request.json()
        except Exception as exc:
            raise ValidationError() from exc
        try:
            return NormalizedAlert.model_validate(payload)
        except (PydanticValidationError, ValueError, TypeError) as exc:
            raise ValidationError() from exc

    def _notification_requests_for_recipients(self, alert: NormalizedAlert, recipients):
        message = NotificationMessage(
            title=alert.title,
            body=alert.body,
            context=NotificationContext(
                kind="alert",
                data={
                    "alert_id": alert.alert_id,
                    "category": alert.category,
                    "event_type": alert.event_type,
                    "severity": alert.severity,
                    "attributes": alert.attributes,
                },
            ),
        )
        out = []
        for row in recipients:
            recipient_id = row.get("recipient_id")
            channel = row.get("channel")
            endpoint_key = row.get("endpoint_key")
            if (
                not isinstance(recipient_id, str)
                or not recipient_id
                or not isinstance(channel, str)
                or not channel
                or not isinstance(endpoint_key, str)
                or not endpoint_key
            ):
                continue

            out.append(
                NotificationRequest(
                    channel=channel,
                    recipient_id=recipient_id,
                    endpoint_key=endpoint_key,
                    message=message,
                )
            )
        return out

    async def process_normalized_alert(self, messenger, payload):
        recipients = await SubscriptionRpcProxy(messenger).get_recipients_for_alert(
            alert=payload
        )
        if not recipients:
            return []
        return self._notification_requests_for_recipients(payload, recipients)
