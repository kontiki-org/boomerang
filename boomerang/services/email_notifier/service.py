from aiohttp.web import HTTPUnprocessableEntity
from kontiki.messaging import Messenger, on_event, rpc, rpc_error
from kontiki.registry import degraded_on
from kontiki.web import http

from boomerang.core.authentication import (
    AuthSessionDelegate,
    requires_identity_auth,
    requires_identity_auth_rpc,
)
from boomerang.core.service_contracts.email_notifier.service import EMAIL_NOTIFIER_SERVICE_NAME
from boomerang.core.contracts.notification.message import (
    NotificationError,
    NotificationOutcome,
    NotificationRequest,
)
from boomerang.core.contracts.notification.endpoint import CreateEndpointRequest
from boomerang.core.exceptions import AuthError, NotFoundError, ValidationError
from boomerang.services.email_notifier.delegate import EmailNotifierDelegate


class EmailNotifierService:
    name = EMAIL_NOTIFIER_SERVICE_NAME
    delegate = EmailNotifierDelegate()
    messenger = Messenger()
    auth_delegate = AuthSessionDelegate(messenger)
    http_error_handlers = {
        ValidationError: (422, ValidationError.message),
        HTTPUnprocessableEntity: (422, ValidationError.message),
        AuthError: (401, AuthError.message),
        NotFoundError: (404, NotFoundError.message),
    }

    @rpc
    async def get_notification_channel_catalog(self):
        catalog = await self.delegate.get_notification_channel_catalog()
        return catalog.model_dump(mode="json", exclude_none=True)

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def create_endpoint(self, body, user_id, email, _headers):
        _ = (email, _headers)
        return await self.delegate.create_endpoint(user_id, body)

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def list_endpoints(self, user_id, email, _headers):
        _ = (email, _headers)
        return await self.delegate.list_endpoints(user_id)

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def get_endpoint(self, endpoint_key, user_id, email, _headers):
        _ = (email, _headers)
        try:
            return await self.delegate.get_endpoint(user_id, endpoint_key)
        except NotFoundError as exc:
            return rpc_error(exc.code, exc.message)

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def delete_endpoint(self, endpoint_key, user_id, email, _headers):
        _ = (email, _headers)
        try:
            return await self.delegate.delete_endpoint(user_id, endpoint_key)
        except NotFoundError as exc:
            return rpc_error(exc.code, exc.message)

    @http(
        "/endpoints",
        "POST",
        version="v1",
        request_model=CreateEndpointRequest,
        validate_request=True,
        errors=[ValidationError, AuthError],
    )
    @requires_identity_auth
    async def create_endpoint_http(self, request, body, user_id, email):
        _ = (request, email)
        return await self.delegate.create_endpoint(user_id, body)

    @http(
        "/endpoints",
        "GET",
        version="v1",
        errors=[AuthError],
    )
    @requires_identity_auth
    async def list_endpoints_http(self, request, user_id, email):
        _ = (request, email)
        return await self.delegate.list_endpoints(user_id)

    @http(
        "/endpoints/{endpoint_key}",
        "GET",
        version="v1",
        errors=[AuthError, ValidationError, NotFoundError],
    )
    @requires_identity_auth
    async def get_endpoint_http(self, request, endpoint_key, user_id, email):
        _ = (request, email)
        return await self.delegate.get_endpoint(user_id, endpoint_key)

    @http(
        "/endpoints/{endpoint_key}",
        "DELETE",
        version="v1",
        errors=[AuthError, ValidationError, NotFoundError],
    )
    @requires_identity_auth
    async def delete_endpoint_http(self, request, endpoint_key, user_id, email):
        _ = (request, email)
        return await self.delegate.delete_endpoint(user_id, endpoint_key)

    @rpc
    async def ensure_auth_email_endpoint(
        self,
        user_id: str,
        endpoint_key: str,
        address: str,
    ):
        normalized_user_id = (user_id or "").strip()
        normalized_endpoint_key = (endpoint_key or "").strip()
        normalized_address = (address or "").strip().lower()
        if (
            not normalized_user_id
            or not normalized_endpoint_key
            or not normalized_address
        ):
            raise ValidationError()
        return await self.delegate.ensure_auth_email_endpoint(
            user_id=normalized_user_id,
            endpoint_key=normalized_endpoint_key,
            address=normalized_address,
        )

    @on_event("email.alerting.notification.requested")
    async def on_notification_requested(self, payload):
        request = (
            payload
            if isinstance(payload, NotificationRequest)
            else NotificationRequest.model_validate(payload)
        )
        try:
            await self.delegate.send_notification_email(request)
        except Exception as exc:
            await self.messenger.publish(
                "alerting.notification.failed",
                NotificationOutcome(
                    status="failed",
                    channel=request.channel,
                    message=request.message,
                    error=NotificationError(
                        type="delivery_error",
                        message=str(exc),
                    ),
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

    @degraded_on
    def is_degraded(self):
        return self.delegate.is_degraded_due_to_smtp_failures()
