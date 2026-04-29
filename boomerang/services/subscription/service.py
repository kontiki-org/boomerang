from aiohttp.web import HTTPUnprocessableEntity
from kontiki.messaging import Messenger, rpc, rpc_error
from kontiki.web import http

from boomerang.core.auth import requires_identity_auth, requires_identity_auth_rpc
from boomerang.core.contracts.subscription import (
    CreateSubscriptionRequest,
    UpdateSubscriptionRequest,
)
from boomerang.core.exceptions import AuthError, NotFoundError, ValidationError
from boomerang.services.subscription.delegate import SubscriptionDelegate
from boomerang.core.contracts.subscription.service import SUBSCRIPTION_SERVICE_NAME


class SubscriptionService:
    name = SUBSCRIPTION_SERVICE_NAME
    delegate = SubscriptionDelegate()
    messenger = Messenger()
    http_error_handlers = {
        ValidationError: (422, ValidationError.message),
        HTTPUnprocessableEntity: (422, ValidationError.message),
        AuthError: (401, AuthError.message),
        NotFoundError: (404, NotFoundError.message),
    }

    @rpc
    async def get_recipients_for_alert(
        self,
        area_type,
        area_value,
        severity,
        category,
        event_type,
    ):
        return await self.delegate.get_recipients_for_alert(
            area_type=area_type,
            area_value=area_value,
            severity=severity,
            category=category,
            event_type=event_type,
        )

    @rpc
    async def attach_channel_endpoint(
        self,
        user_id: str,
        channel: str,
        endpoint_key: str,
        is_default: bool = False,
    ):
        return await self.delegate.attach_channel_endpoint(
            user_id=user_id,
            channel=channel,
            endpoint_key=endpoint_key,
            is_default=is_default,
        )

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def create_subscription(self, body, user_id, email, _headers):
        return await self.delegate.create_subscription(body, user_id)

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def update_subscription(
        self, subscription_id, body, user_id, email, _headers
    ):
        return await self.delegate.update_subscription(subscription_id, body, user_id)

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def delete_subscription(self, subscription_id, user_id, email, _headers):
        try:
            return await self.delegate.delete_subscription(subscription_id, user_id)
        except NotFoundError as exc:
            return rpc_error(exc.code, exc.message)

    @rpc
    async def get_channels(self):
        return await self.delegate.get_channels()

    @rpc
    async def get_alerts(self):
        return await self.delegate.get_alerts()

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def get_subscriptions(self, user_id, email, _headers):
        return await self.delegate.get_subscriptions(user_id)

    @rpc
    # --------------------------------------------------------------------------
    # HTTP endpoints
    # --------------------------------------------------------------------------
    @http(
        "/subscriptions",
        "POST",
        version="v1",
        request_model=CreateSubscriptionRequest,
        validate_request=True,
        errors=[ValidationError, AuthError],
    )
    @requires_identity_auth
    async def create_subscription_http(self, request, body, user_id, email):
        _ = email
        return await self.delegate.create_subscription(body, user_id)

    @http("/subscriptions", "GET", version="v1", errors=[AuthError])
    @requires_identity_auth
    async def get_subscriptions_http(self, request, user_id, email):
        _ = email
        return await self.delegate.get_subscriptions(user_id)

    @http(
        "/subscriptions/{subscription_id}",
        "PATCH",
        version="v1",
        request_model=UpdateSubscriptionRequest,
        validate_request=True,
        errors=[ValidationError, AuthError, NotFoundError],
    )
    @requires_identity_auth
    async def update_subscription_http(
        self, request, subscription_id, body, user_id, email
    ):
        _ = email
        return await self.delegate.update_subscription(subscription_id, body, user_id)

    @http(
        "/subscriptions/{subscription_id}",
        "DELETE",
        version="v1",
        errors=[AuthError, NotFoundError],
    )
    @requires_identity_auth
    async def delete_subscription_http(self, request, subscription_id, user_id, email):
        _ = email
        return await self.delegate.delete_subscription(subscription_id, user_id)

    @http("/channels", "GET", version="v1")
    async def get_channels_http(self, request):
        _ = request
        return await self.delegate.get_channels()

    @http("/alerts", "GET", version="v1")
    async def get_alerts_http(self, request):
        _ = request
        return await self.delegate.get_alerts()
