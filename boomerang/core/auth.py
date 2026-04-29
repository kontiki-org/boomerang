import logging
from functools import wraps

from kontiki.messaging import rpc_error

from boomerang.core.contracts.identity.service import IdentityRpcProxy
from boomerang.core.exceptions import AuthError


async def require_authenticated_session(auth_header, messenger):
    if not isinstance(auth_header, str):
        logging.warning(f"Invalid authentication header: {auth_header}")
        raise AuthError()
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        logging.warning(f"Invalid authentication header: {auth_header}")
        raise AuthError()

    access_token = token.strip()
    rpc_client = IdentityRpcProxy(messenger)
    try:
        return await rpc_client.verify_session(access_token)
    except Exception as exc:
        logging.warning(f"Failed to verify session: {exc}")
        raise AuthError() from exc


def requires_identity_auth_rpc(handler):
    @wraps(handler)
    async def wrapper(self, _headers, *args, **kwargs):
        if not isinstance(_headers, dict):
            return rpc_error(AuthError.code, AuthError.message)
        auth_header = _headers.get("Authorization", "")
        try:
            session = await require_authenticated_session(
                auth_header=auth_header,
                messenger=self.messenger,
            )
        except AuthError:
            return rpc_error(AuthError.code, AuthError.message)
        return await handler(
            self,
            *args,
            user_id=session["user_id"],
            email=session["email"],
            _headers=_headers,
            **kwargs,
        )

    return wrapper


def requires_identity_auth(handler):
    @wraps(handler)
    async def wrapper(self, request, *args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        session = await require_authenticated_session(
            auth_header=auth_header,
            messenger=self.messenger,
        )
        return await handler(
            self,
            request,
            *args,
            user_id=session["user_id"],
            email=session["email"],
            **kwargs,
        )

    return wrapper
