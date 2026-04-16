import logging
from aiohttp.web import HTTPUnprocessableEntity
from kontiki.messaging import Messenger, RpcProxy, rpc
from kontiki.web import http

from boomerang.services.subscription.delegate import SubscriptionDelegate
from boomerang.services.subscription.exceptions import (
    AuthError,
    NotFoundError,
    ValidationError,
)
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

    @staticmethod
    def requires_auth(handler):
        async def wrapper(self, request, *args, **kwargs):
            session = await self._require_authenticated_session(request)
            return await handler(
                self,
                request,
                *args,
                user_id=session["user_id"],
                email=session["email"],
                **kwargs,
            )

        return wrapper

    async def _require_authenticated_session(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not isinstance(auth_header, str):
            raise AuthError("Authentication required or invalid.")
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise AuthError("Authentication required or invalid.")
        access_token = token.strip()

        rpc_client = RpcProxy(self.messenger, "identity-service")
        try:
            session = await rpc_client.verify_session(access_token)
        except Exception as exc:
            logging.error("Authentication required or invalid.", exc_info=exc)
            raise AuthError("Authentication required or invalid.") from exc

        return session

    @rpc
    async def get_recipients_for_zone(self, zone_code, severity, category):
        return await self.delegate.get_recipients_for_zone(
            zone_code, severity, category
        )

    @http(
        "/subscriptions",
        "POST",
        version="v1",
        request_model=CreateSubscriptionRequest,
        validate_request=True,
        errors=[ValidationError, AuthError],
    )
    @requires_auth
    async def create_subscription(self, request, body, user_id, email):
        _ = email
        return await self.delegate.create_subscription(body, user_id)

    @http("/subscriptions", "GET", version="v1", errors=[AuthError])
    @requires_auth
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
    @requires_auth
    async def update_subscription(self, request, subscription_id, body, user_id, email):
        _ = email
        return await self.delegate.update_subscription(subscription_id, body, user_id)

    @http(
        "/subscriptions/{subscription_id}",
        "DELETE",
        version="v1",
        errors=[AuthError, NotFoundError],
    )
    @requires_auth
    async def delete_subscription(self, request, subscription_id, user_id, email):
        _ = email
        return await self.delegate.delete_subscription(subscription_id, user_id)

    @http("/channels", "POST", version="v1", errors=[ValidationError, AuthError])
    async def upsert_channel(self, request):
        return await self.delegate.upsert_channel()

    @http("/channels", "GET", version="v1")
    async def list_channels(self, request):
        _ = request
        return await self.delegate.list_channels()

    @http(
        "/channels/{channel_id}",
        "PATCH",
        version="v1",
        errors=[ValidationError, AuthError, NotFoundError],
    )
    async def update_channel(self, request):
        _ = request
        return await self.delegate.update_channel()

    @http(
        "/channels/{channel_id}",
        "DELETE",
        version="v1",
        errors=[AuthError, NotFoundError],
    )
    async def delete_channel(self, request):
        _ = request
        return await self.delegate.delete_channel()

    @http("/categories", "GET", version="v1")
    async def list_categories(self, request):
        _ = request
        return await self.delegate.list_categories()
