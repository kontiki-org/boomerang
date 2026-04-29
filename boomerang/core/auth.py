from functools import wraps

from kontiki.messaging import RpcProxy

from boomerang.core.exceptions import AuthError

IDENTITY_SERVICE_NAME = "identity-service"


async def require_authenticated_session(
    request,
    messenger,
):
    auth_header = request.headers.get("Authorization", "")
    if not isinstance(auth_header, str):
        raise AuthError()
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise AuthError()

    access_token = token.strip()
    rpc_client = RpcProxy(messenger, IDENTITY_SERVICE_NAME)
    try:
        return await rpc_client.verify_session(access_token)
    except Exception as exc:
        raise AuthError() from exc


def requires_identity_auth(handler):
    @wraps(handler)
    async def wrapper(self, request, *args, **kwargs):
        session = await require_authenticated_session(
            request=request,
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
