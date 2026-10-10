from aiohttp.web import Response
from kontiki.web import http

from boomerang.core.exceptions import AuthError, NotFoundError
from boomerang.services.notifiers.common.sentinel import SentinelDelegate


class SentinelHttp:
    sentinel = SentinelDelegate(None)

    http_error_handlers = {
        AuthError: (401, AuthError.message),
        NotFoundError: (404, NotFoundError.message),
    }

    @http(
        "/watchdogs/{name}/heartbeat",
        "POST",
        status_code=204,
        errors=[AuthError, NotFoundError],
    )
    async def post_watchdog_heartbeat(self, request, name):
        self.sentinel.observe_heartbeat(request, name)
        return Response(status=204)
