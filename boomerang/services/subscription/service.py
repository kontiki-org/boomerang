from aiohttp.web import HTTPUnprocessableEntity
from kontiki.messaging import Messenger, rpc, rpc_error
from kontiki.web import http

from boomerang.core.authentication import (
    AuthSessionDelegate,
    requires_identity_auth,
    requires_identity_auth_rpc,
)
from boomerang.core.contracts.notification_endpoint import (
    CreateChannelEndpointRequest,
    CreateEndpointRequest,
)
from boomerang.core.contracts.subscription import (
    CreateSubscriptionRequest,
    UpdateSubscriptionRequest,
)
from boomerang.core.contracts.subscription.service import SUBSCRIPTION_SERVICE_NAME
from boomerang.core.exceptions import AuthError, NotFoundError, ValidationError
from boomerang.services.subscription.delegate import SubscriptionDelegate


def _authorization_headers(headers):
    if headers is None:
        return {}
    if isinstance(headers, dict):
        authorization = headers.get("Authorization") or headers.get("authorization")
    else:
        authorization = headers.get("Authorization") or headers.get("authorization")
    if authorization:
        return {"Authorization": authorization}
    return {}


class SubscriptionService:
    name = SUBSCRIPTION_SERVICE_NAME
    delegate = SubscriptionDelegate()
    messenger = Messenger()
    auth_delegate = AuthSessionDelegate(messenger)
    http_error_handlers = {
        ValidationError: (422, ValidationError.message),
        HTTPUnprocessableEntity: (422, ValidationError.message),
        AuthError: (401, AuthError.message),
        NotFoundError: (404, NotFoundError.message),
    }

    @rpc
    async def get_recipients_for_alert(self, alert):
        return await self.delegate.get_recipients_for_alert(alert=alert)

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
    async def get_alert_subscription_catalog(self):
        catalog = await self.delegate.get_alert_subscription_catalog(self.messenger)
        return catalog.model_dump(mode="json")

    @rpc
    async def get_notification_channels_catalog(self):
        catalog = await self.delegate.get_notification_channels_catalog(self.messenger)
        return catalog.model_dump(mode="json", exclude_none=True)

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def create_endpoint(self, body, user_id, email, _headers):
        _ = email
        return await self.delegate.create_endpoint(
            body,
            user_id,
            _authorization_headers(_headers),
            self.messenger,
        )

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def list_endpoints(self, user_id, email, _headers):
        _ = email
        return await self.delegate.list_endpoints(
            user_id,
            _authorization_headers(_headers),
            self.messenger,
        )

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def get_endpoint(self, channel_id, endpoint_key, user_id, email, _headers):
        _ = email
        try:
            return await self.delegate.get_endpoint(
                channel_id,
                endpoint_key,
                user_id,
                _authorization_headers(_headers),
                self.messenger,
            )
        except NotFoundError as exc:
            return rpc_error(exc.code, exc.message)

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def delete_endpoint(self, channel_id, endpoint_key, user_id, email, _headers):
        _ = email
        try:
            return await self.delegate.delete_endpoint(
                channel_id,
                endpoint_key,
                user_id,
                _authorization_headers(_headers),
                self.messenger,
            )
        except NotFoundError as exc:
            return rpc_error(exc.code, exc.message)

    @rpc(include_headers=True)
    @requires_identity_auth_rpc
    async def get_subscriptions(self, user_id, email, _headers):
        return await self.delegate.get_subscriptions(user_id)

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

    @http("/alert-catalog", "GET", version="v1")
    async def get_alert_subscription_catalog_http(self, request):
        _ = request
        catalog = await self.delegate.get_alert_subscription_catalog(self.messenger)
        return catalog.model_dump(mode="json")

    @http("/notification-channels/catalog", "GET", version="v1")
    async def get_notification_channels_catalog_http(self, request):
        _ = request
        catalog = await self.delegate.get_notification_channels_catalog(self.messenger)
        return catalog.model_dump(mode="json", exclude_none=True)

    @http(
        "/endpoints",
        "POST",
        version="v1",
        request_model=CreateChannelEndpointRequest,
        validate_request=True,
        errors=[ValidationError, AuthError],
    )
    @requires_identity_auth
    async def create_endpoint_http(self, request, body, user_id, email):
        _ = (request, email)
        return await self.delegate.create_endpoint(
            body,
            user_id,
            _authorization_headers(request.headers),
            self.messenger,
        )

    @http("/endpoints", "GET", version="v1", errors=[AuthError])
    @requires_identity_auth
    async def list_endpoints_http(self, request, user_id, email):
        _ = email
        return await self.delegate.list_endpoints(
            user_id,
            _authorization_headers(request.headers),
            self.messenger,
        )

    @http(
        "/endpoints/{channel_id}/{endpoint_key}",
        "GET",
        version="v1",
        errors=[AuthError, ValidationError, NotFoundError],
    )
    @requires_identity_auth
    async def get_endpoint_http(
        self,
        request,
        channel_id,
        endpoint_key,
        user_id,
        email,
    ):
        _ = email
        return await self.delegate.get_endpoint(
            channel_id,
            endpoint_key,
            user_id,
            _authorization_headers(request.headers),
            self.messenger,
        )

    @http(
        "/endpoints/{channel_id}/{endpoint_key}",
        "DELETE",
        version="v1",
        errors=[AuthError, ValidationError, NotFoundError],
    )
    @requires_identity_auth
    async def delete_endpoint_http(
        self,
        request,
        channel_id,
        endpoint_key,
        user_id,
        email,
    ):
        _ = email
        return await self.delegate.delete_endpoint(
            channel_id,
            endpoint_key,
            user_id,
            _authorization_headers(request.headers),
            self.messenger,
        )
