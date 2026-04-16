from aiohttp.web import HTTPUnprocessableEntity
from kontiki.messaging import Messenger, rpc
from kontiki.web import http

from boomerang.core.auth import AuthError, requires_identity_auth
from boomerang.services.subscription.delegate import SubscriptionDelegate
from boomerang.services.subscription.exceptions import NotFoundError, ValidationError
from boomerang.services.subscription.http_models import (
    CreateSubscriptionRequest,
    UpdateSubscriptionRequest,
)


class SubscriptionService:
    name = "subscription-service"
    delegate = SubscriptionDelegate()
    messenger = Messenger()
    http_error_handlers = {
        ValidationError: (422, "Invalid request payload."),
        HTTPUnprocessableEntity: (422, "Invalid request payload."),
        AuthError: (401, "Authentication required or invalid."),
        NotFoundError: (404, "Resource not found."),
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

    @http(
        "/subscriptions",
        "POST",
        version="v1",
        request_model=CreateSubscriptionRequest,
        validate_request=True,
        errors=[ValidationError, AuthError],
    )
    @requires_identity_auth
    async def create_subscription(self, request, body, user_id, email):
        _ = email
        return await self.delegate.create_subscription(body, user_id)

    @http("/subscriptions", "GET", version="v1", errors=[AuthError])
    @requires_identity_auth
    async def list_subscriptions(self, request, user_id, email):
        _ = email
        return await self.delegate.list_subscriptions(user_id)

    @http(
        "/subscriptions/{subscription_id}",
        "PATCH",
        version="v1",
        request_model=UpdateSubscriptionRequest,
        validate_request=True,
        errors=[ValidationError, AuthError, NotFoundError],
    )
    @requires_identity_auth
    async def update_subscription(self, request, subscription_id, body, user_id, email):
        _ = email
        return await self.delegate.update_subscription(subscription_id, body, user_id)

    @http(
        "/subscriptions/{subscription_id}",
        "DELETE",
        version="v1",
        errors=[AuthError, NotFoundError],
    )
    @requires_identity_auth
    async def delete_subscription(self, request, subscription_id, user_id, email):
        _ = email
        return await self.delegate.delete_subscription(subscription_id, user_id)

    @http("/channels", "GET", version="v1")
    async def list_channels(self, request):
        _ = request
        return await self.delegate.list_channels()

    @http("/alerts", "GET", version="v1")
    async def list_alerts(self, request):
        _ = request
        return await self.delegate.list_alerts()
