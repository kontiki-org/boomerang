from aiohttp.web import HTTPUnprocessableEntity
from kontiki.messaging import Messenger, on_event, rpc, rpc_error
from kontiki.web import http

from boomerang.core.auth import AuthError, requires_identity_auth, requires_identity_auth_rpc
from boomerang.core.contracts.notification import (
    NotificationError,
    NotificationOutcome,
    NotificationRequest,
)
from boomerang.core.exceptions import ValidationError, NotFoundError
from boomerang.services.email_notifier.delegate import EmailNotifierDelegate
from boomerang.services.email_notifier.http_models import CreateEmailEndpointRequest


class EmailNotifierService:
    name = "email-notifier-service"
    delegate = EmailNotifierDelegate()
    messenger = Messenger()
    http_error_handlers = {
        ValidationError: (422, ValidationError.message),
        HTTPUnprocessableEntity: (422, ValidationError.message),
        AuthError: (401, AuthError.message),
        NotFoundError: (404, NotFoundError.message),
    }

    # --------------------------------------------------------------------------
    # RPC endpoints
    # --------------------------------------------------------------------------

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def create_email_endpoint(self, body, user_id, email, _headers):
        _ = (email, _headers)
        return await self.delegate.create_email_endpoint(user_id, body)

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def list_email_endpoints(self, user_id, email, _headers):
        _ = (email, _headers)
        return await self.delegate.list_email_endpoints(user_id)

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def get_email_endpoint(self, endpoint_key, user_id, email, _headers):
        _ = (email, _headers)
        try:
            return await self.delegate.get_email_endpoint(user_id, endpoint_key)
        except NotFoundError as exc:
            return rpc_error(exc.code, exc.message)

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def delete_email_endpoint(self, endpoint_key, user_id, email, _headers):
        _ = (email, _headers)
        try:
            return await self.delegate.delete_email_endpoint(user_id, endpoint_key)
        except NotFoundError as exc:
            return rpc_error(exc.code, exc.message)

    # --------------------------------------------------------------------------
    # HTTP endpoints
    # --------------------------------------------------------------------------
    @http(
        "/email/endpoints",
        "POST",
        version="v1",
        request_model=CreateEmailEndpointRequest,
        validate_request=True,
        errors=[ValidationError, AuthError],
    )
    @requires_identity_auth
    async def create_email_endpoint_http(self, request, body, user_id, email):
        _ = (request, email)
        return await self.delegate.create_email_endpoint(user_id, body)

    @http(
        "/email/endpoints",
        "GET",
        version="v1",
        errors=[AuthError],
    )
    @requires_identity_auth
    async def list_email_endpoints_http(self, request, user_id, email):
        _ = (request, email)
        return await self.delegate.list_email_endpoints(user_id)

    @http(
        "/email/endpoints/{endpoint_key}",
        "GET",
        version="v1",
        errors=[AuthError, ValidationError, NotFoundError],
    )
    @requires_identity_auth
    async def get_email_endpoint_http(self, request, endpoint_key, user_id, email):
        _ = (request, email)
        return await self.delegate.get_email_endpoint(user_id, endpoint_key)

    @http(
        "/email/endpoints/{endpoint_key}",
        "DELETE",
        version="v1",
        errors=[AuthError, ValidationError, NotFoundError],
    )
    @requires_identity_auth
    async def delete_email_endpoint_http(self, request, endpoint_key, user_id, email):
        _ = (request, email)
        return await self.delegate.delete_email_endpoint(user_id, endpoint_key)

    # --------------------------------------------------------------------------
    # Internal system endpoints
    # --------------------------------------------------------------------------

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
