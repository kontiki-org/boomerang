from aiohttp.web import HTTPUnprocessableEntity
from kontiki.messaging import Messenger
from kontiki.web import http

from boomerang.core.auth import AuthError, requires_identity_auth
from boomerang.services.email_notifier.delegate import EmailNotifierDelegate
from boomerang.services.email_notifier.exceptions import NotFoundError, ValidationError
from boomerang.services.email_notifier.http_models import CreateEmailEndpointRequest


class EmailNotifierService:
    name = "email-notifier-service"
    delegate = EmailNotifierDelegate()
    messenger = Messenger()
    http_error_handlers = {
        ValidationError: (422, "Invalid request payload."),
        HTTPUnprocessableEntity: (422, "Invalid request payload."),
        AuthError: (401, "Authentication required or invalid."),
        NotFoundError: (404, "Resource not found."),
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

    @http(
        "/email/endpoints",
        "GET",
        version="v1",
        errors=[AuthError],
    )
    @requires_identity_auth
    async def list_email_endpoints(self, request, user_id, email):
        _ = (request, email)
        return await self.delegate.list_email_endpoints(user_id)

    @http(
        "/email/endpoints/{endpoint_key}",
        "GET",
        version="v1",
        errors=[AuthError, ValidationError, NotFoundError],
    )
    @requires_identity_auth
    async def get_email_endpoint(self, request, endpoint_key, user_id, email):
        _ = (request, email)
        return await self.delegate.get_email_endpoint(user_id, endpoint_key)

    @http(
        "/email/endpoints/{endpoint_key}",
        "DELETE",
        version="v1",
        errors=[AuthError, ValidationError, NotFoundError],
    )
    @requires_identity_auth
    async def delete_email_endpoint(self, request, endpoint_key, user_id, email):
        _ = (request, email)
        return await self.delegate.delete_email_endpoint(user_id, endpoint_key)
