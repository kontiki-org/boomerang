from functools import wraps

from kontiki.messaging import rpc_error

from boomerang.core.authentication.auth_delegate import AuthSessionDelegate
from boomerang.core.exceptions import AuthError


async def require_authenticated_session(auth_header, auth_delegate):
    return await auth_delegate.require_authenticated_session(
        auth_header=auth_header,
    )


def requires_identity_auth_rpc(handler):
    @wraps(handler)
    async def wrapper(self, _headers, *args, **kwargs):
        if not isinstance(_headers, dict):
            return rpc_error(AuthError.code, AuthError.message)
        auth_delegate = getattr(self, "auth_delegate", None)
        if not isinstance(auth_delegate, AuthSessionDelegate):
            return rpc_error(AuthError.code, AuthError.message)
        auth_header = _headers.get("Authorization", "")
        try:
            session = await require_authenticated_session(
                auth_header=auth_header,
                auth_delegate=auth_delegate,
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
        auth_delegate = getattr(self, "auth_delegate", None)
        if not isinstance(auth_delegate, AuthSessionDelegate):
            raise AuthError()
        auth_header = request.headers.get("Authorization", "")
        session = await require_authenticated_session(
            auth_header=auth_header,
            auth_delegate=auth_delegate,
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
