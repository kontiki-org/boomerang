import logging

from aiohttp.web import HTTPUnprocessableEntity
from kontiki.messaging import Messenger, rpc
from kontiki.web import http

from boomerang.services.identity.delegate import IdentityDelegate
from boomerang.services.identity.exceptions import (
    AuthError,
    DependencyError,
    RateLimitError,
    ValidationError,
)


class IdentityService:
    name = "identity-service"
    delegate = IdentityDelegate()
    messenger = Messenger()
    http_error_handlers = {
        ValidationError: (422, "Invalid request payload."),
        HTTPUnprocessableEntity: (422, "Invalid request payload."),
        AuthError: (401, "Authentication required or invalid."),
        RateLimitError: (429, "Too many requests. Please try again later."),
        DependencyError: (503, "Temporary service dependency failure."),
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

    @http(
        "/auth/request-auth-code",
        "POST",
        version="v1",
        errors=[ValidationError, RateLimitError],
    )
    async def request_auth_code(self, request):
        logging.info("request_auth_code called with request=%s", request)
        outcome = await self.delegate.request_auth_code(request, self.messenger)
        return await self._finalize_entrypoint(outcome)

    @http(
        "/auth/consume-auth-code",
        "POST",
        version="v1",
        errors=[ValidationError, AuthError, RateLimitError],
    )
    async def consume_auth_code(self, request):
        logging.info("consume_auth_code called with request=%s", request)
        outcome = await self.delegate.consume_auth_code(request)
        return await self._finalize_entrypoint(outcome)

    @rpc
    async def verify_session(self, access_token: str):
        return await self.delegate.verify_session(access_token)
