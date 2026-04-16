from aiohttp.web import HTTPUnprocessableEntity
from kontiki.messaging import Messenger
from kontiki.web import http

from boomerang.core.auth import AuthError, requires_identity_auth
from boomerang.services.email_notifier.delegate import EmailNotifierDelegate
from boomerang.services.email_notifier.exceptions import ValidationError
from boomerang.services.email_notifier.http_models import CreateEmailEndpointRequest


class EmailNotifierService:
    name = "email-notifier-service"
    delegate = EmailNotifierDelegate()
    messenger = Messenger()
    http_error_handlers = {
        ValidationError: (422, "Invalid request payload."),
        HTTPUnprocessableEntity: (422, "Invalid request payload."),
        AuthError: (401, "Authentication required or invalid."),
    }

    @http(
        "/email/endpoints",
        "POST",
        version="v1",
        request_model=CreateEmailEndpointRequest,
        validate_request=True,
        errors=[ValidationError, AuthError],
    )
    @requires_identity_auth
    async def create_email_endpoint(self, request, body, user_id, email):
        _ = (request, email)
        return await self.delegate.create_email_endpoint(user_id, body)
