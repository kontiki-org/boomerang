from aiohttp.web import HTTPUnprocessableEntity
from kontiki.messaging import Messenger, on_event
from kontiki.web import http

from boomerang.core.auth import AuthError, requires_identity_auth
from boomerang.core.contracts.notification import (
    NotificationError,
    NotificationOutcome,
    NotificationRequest,
)
from boomerang.services.sms_notifier.delegate import SmsNotifierDelegate
from boomerang.services.sms_notifier.exceptions import NotFoundError, ValidationError
from boomerang.services.sms_notifier.http_models import CreateSmsEndpointRequest


class SmsNotifierService:
    name = "sms-notifier-service"
    delegate = SmsNotifierDelegate()
    messenger = Messenger()
    http_error_handlers = {
        ValidationError: (422, "Invalid request payload."),
        HTTPUnprocessableEntity: (422, "Invalid request payload."),
        AuthError: (401, "Authentication required or invalid."),
        NotFoundError: (404, "Resource not found."),
    }

    @http(
        "/sms/endpoints",
        "POST",
        version="v1",
        request_model=CreateSmsEndpointRequest,
        validate_request=True,
        errors=[ValidationError, AuthError],
    )
    @requires_identity_auth
    async def create_sms_endpoint(self, request, body, user_id, email):
        _ = (request, email)
        return await self.delegate.create_sms_endpoint(user_id, body)

    @http(
        "/sms/endpoints",
        "GET",
        version="v1",
        errors=[AuthError],
    )
    @requires_identity_auth
    async def list_sms_endpoints(self, request, user_id, email):
        _ = (request, email)
        return await self.delegate.list_sms_endpoints(user_id)

    @http(
        "/sms/endpoints/{endpoint_key}",
        "GET",
        version="v1",
        errors=[AuthError, ValidationError, NotFoundError],
    )
    @requires_identity_auth
    async def get_sms_endpoint(self, request, endpoint_key, user_id, email):
        _ = (request, email)
        return await self.delegate.get_sms_endpoint(user_id, endpoint_key)

    @http(
        "/sms/endpoints/{endpoint_key}",
        "DELETE",
        version="v1",
        errors=[AuthError, ValidationError, NotFoundError],
    )
    @requires_identity_auth
    async def delete_sms_endpoint(self, request, endpoint_key, user_id, email):
        _ = (request, email)
        return await self.delegate.delete_sms_endpoint(user_id, endpoint_key)

    @on_event("sms.alerting.notification.requested")
    async def on_notification_requested(self, payload):
        request = (
            payload
            if isinstance(payload, NotificationRequest)
            else NotificationRequest.model_validate(payload)
        )
        try:
            await self.delegate.send_notification_sms(request)
        except Exception as exc:
            await self.messenger.publish(
                "alerting.notification.failed",
                NotificationOutcome(
                    status="failed",
                    channel=request.channel,
                    message=request.message,
                    error=NotificationError(type="delivery_error", message=str(exc)),
                ),
            )
            return
        await self.messenger.publish(
            "alerting.notification.delivered",
            NotificationOutcome(
                status="delivered",
                channel=request.channel,
                message=request.message,
            ),
        )
