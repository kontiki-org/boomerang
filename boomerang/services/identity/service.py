import logging

from aiohttp.web import HTTPUnprocessableEntity
from kontiki.messaging import Messenger, rpc, rpc_error
from kontiki.web import http
from pydantic import ValidationError as PydanticValidationError

from boomerang.core.exceptions import AuthError, ValidationError
from boomerang.services.identity.delegate import IdentityDelegate
from boomerang.services.identity.exceptions import DependencyError, RateLimitError
from boomerang.services.identity.http_models import (
    ConsumeAuthCodeRequest,
    RequestAuthCodeRequest,
)


class IdentityService:
    name = "identity-service"
    delegate = IdentityDelegate()
    messenger = Messenger()
    http_error_handlers = {
        ValidationError: (422, ValidationError.message),
        HTTPUnprocessableEntity: (422, ValidationError.message),
        AuthError: (401, AuthError.message),
        RateLimitError: (429, RateLimitError.message),
        DependencyError: (503, DependencyError.message),
    }

    @http(
        "/auth/request-auth-code",
        "POST",
        version="v1",
        errors=[ValidationError, RateLimitError],
    )
    async def request_auth_code_http(self, request):
        logging.info("request_auth_code called with request=%s", request)
        try:
            body = await request.json()
        except Exception as exc:
            raise ValidationError() from exc

        try:
            model = RequestAuthCodeRequest.model_validate(body)
        except PydanticValidationError as exc:
            raise ValidationError() from exc

        return await self.delegate.request_auth_code(model.email, self.messenger)

    @http(
        "/auth/consume-auth-code",
        "POST",
        version="v1",
        errors=[ValidationError, AuthError, RateLimitError],
    )
    async def consume_auth_code_http(self, request):
        try:
            body = await request.json()
        except Exception as exc:
            raise ValidationError() from exc

        try:
            model = ConsumeAuthCodeRequest.model_validate(body)
        except PydanticValidationError as exc:
            raise ValidationError() from exc
        logging.info("consume_auth_code called with request=%s", request)
        return await self.delegate.consume_auth_code(model.code)

    # RPC endpoints

    @rpc
    async def request_auth_code(self, email: str):
        try:
            return await self.delegate.request_auth_code(email, self.messenger)
        except RateLimitError as exc:
            return rpc_error(exc.code, exc.message)

    @rpc
    async def consume_auth_code(self, code: str):
        try:
            return await self.delegate.consume_auth_code(code)
        except (AuthError, RateLimitError) as exc:
            return rpc_error(exc.code, exc.message)

    @rpc
    async def verify_session(self, access_token: str):
        try:
            return await self.delegate.verify_session(access_token)
        except AuthError as exc:
            return rpc_error(exc.code, exc.message)
