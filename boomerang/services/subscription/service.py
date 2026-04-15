from kontiki.messaging import Messenger, rpc
from kontiki.web import http

from boomerang.services.subscription.delegate import SubscriptionDelegate
from boomerang.services.subscription.exceptions import (
    AuthError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


class SubscriptionService:
    name = "subscription-service"
    delegate = SubscriptionDelegate()
    messenger = Messenger()
    http_error_handlers = {
        ValidationError: (400, "Invalid request payload."),
        AuthError: (401, "Authentication required or invalid."),
        RateLimitError: (429, "Too many requests. Please try again later."),
        NotFoundError: (404, "Resource not found."),
    }

    @rpc
    async def get_recipients_for_zone(self, zone_code, severity, category):
        return await self.delegate.get_recipients_for_zone(zone_code, severity, category)

    @http(
        "/auth/request-magic-link",
        "POST",
        version="v1",
        errors=[ValidationError, RateLimitError],
    )
    async def request_magic_link(self, request):
        outcome = await self.delegate.request_magic_link(request)
        for event in outcome.events:
            await self.messenger.publish(event.event_type, event.payload)
        return outcome.http_response

    @http(
        "/auth/consume-magic-link",
        "POST",
        version="v1",
        errors=[ValidationError, AuthError, RateLimitError],
    )
    async def consume_magic_link(self, request):
        return await self.delegate.consume_magic_link(request)

    @http("/auth/logout", "POST", version="v1", errors=[AuthError])
    async def logout(self, request):
        return await self.delegate.logout(request)

    @http("/auth/me", "GET", version="v1", errors=[AuthError])
    async def me(self, request):
        return await self.delegate.me(request)

    @http(
        "/subscriptions",
        "POST",
        version="v1",
        errors=[ValidationError, AuthError],
    )
    async def create_subscription(self, request):
        return await self.delegate.create_subscription(request)

    @http("/subscriptions", "GET", version="v1", errors=[AuthError])
    async def list_subscriptions(self, request):
        return await self.delegate.list_subscriptions(request)

    @http(
        "/subscriptions/{subscription_id}",
        "PATCH",
        version="v1",
        errors=[ValidationError, AuthError, NotFoundError],
    )
    async def update_subscription(self, request):
        return await self.delegate.update_subscription(request)

    @http(
        "/subscriptions/{subscription_id}",
        "DELETE",
        version="v1",
        errors=[AuthError, NotFoundError],
    )
    async def delete_subscription(self, request):
        return await self.delegate.delete_subscription(request)

    @http("/channels", "POST", version="v1", errors=[ValidationError, AuthError])
    async def upsert_channel(self, request):
        return await self.delegate.upsert_channel(request)

    @http("/channels", "GET", version="v1", errors=[AuthError])
    async def list_channels(self, request):
        return await self.delegate.list_channels(request)

    @http(
        "/channels/{channel_id}",
        "PATCH",
        version="v1",
        errors=[ValidationError, AuthError, NotFoundError],
    )
    async def update_channel(self, request):
        return await self.delegate.update_channel(request)

    @http(
        "/channels/{channel_id}",
        "DELETE",
        version="v1",
        errors=[AuthError, NotFoundError],
    )
    async def delete_channel(self, request):
        return await self.delegate.delete_channel(request)

    @http("/channels/catalog", "GET", version="v1")
    async def list_channel_catalog(self, request):
        return await self.delegate.list_channel_catalog(request)

    @http("/categories", "GET", version="v1")
    async def list_categories(self, request):
        return await self.delegate.list_categories(request)

