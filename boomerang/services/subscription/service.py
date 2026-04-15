import logging

from aiohttp.web import HTTPUnprocessableEntity
from kontiki.messaging import Messenger, rpc
from kontiki.web import http

from boomerang.services.subscription.delegate import SubscriptionDelegate
from boomerang.services.subscription.exceptions import (
    AuthError,
    NotFoundError,
    RateLimitError,
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
        RateLimitError: (429, "Too many requests. Please try again later."),
        NotFoundError: (404, "Resource not found."),
    }

    async def _finalize_entrypoint(self, outcome):
        events = outcome.events or []
        logging.info("produced %s outbound event(s)", len(events))
        for event in events:
            await self.messenger.publish(event.event_type, event.payload)
            logging.info("published event type=%s", event.event_type)
        if outcome.http_status is not None:
            return outcome.http_status, outcome.http_response
        return outcome.http_response

    @rpc
    async def get_recipients_for_zone(self, zone_code, severity, category):
        return await self.delegate.get_recipients_for_zone(
            zone_code, severity, category
        )

    @http(
        "/auth/request-auth-code",
        "POST",
        version="v1",
        errors=[ValidationError, RateLimitError],
    )
    async def request_auth_code(self, request):
        outcome = await self.delegate.request_auth_code(request)
        logging.info("request_auth_code delegate outcome ready")
        return await self._finalize_entrypoint(outcome)

    @http(
        "/auth/consume-auth-code",
        "POST",
        version="v1",
        errors=[ValidationError, AuthError, RateLimitError],
    )
    async def consume_auth_code(self, request):
        outcome = await self.delegate.consume_auth_code(request)
        logging.info("consume_auth_code delegate outcome ready")
        return await self._finalize_entrypoint(outcome)

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
        request_model=CreateSubscriptionRequest,
        validate_request=True,
        errors=[ValidationError, AuthError],
    )
    async def create_subscription(self, request, body):
        return await self.delegate.create_subscription(request, body)

    @http("/subscriptions", "GET", version="v1", errors=[AuthError])
    async def list_subscriptions(self, request):
        return await self.delegate.list_subscriptions(request)

    @http(
        "/subscriptions/{subscription_id}",
        "PATCH",
        version="v1",
        request_model=UpdateSubscriptionRequest,
        validate_request=True,
        errors=[ValidationError, AuthError, NotFoundError],
    )
    async def update_subscription(self, request, subscription_id, body):
        return await self.delegate.update_subscription(request, subscription_id, body)

    @http(
        "/subscriptions/{subscription_id}",
        "DELETE",
        version="v1",
        errors=[AuthError, NotFoundError],
    )
    async def delete_subscription(self, request, subscription_id):
        return await self.delegate.delete_subscription(request, subscription_id)

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
