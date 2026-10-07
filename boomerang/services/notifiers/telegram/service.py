from aiohttp.web import Response
from boomerang_contracts.notification.message import NotificationRequest
from kontiki.messaging import Messenger, on_event, rpc
from kontiki.registry import degraded_on
from kontiki.web import http

from boomerang.core.exceptions import AuthError, NotFoundError
from boomerang.core.service_contracts.notifiers.telegram.service import (
    TELEGRAM_NOTIFIER_SERVICE_NAME,
)
from boomerang.services.notifiers.common.sentinel import SentinelDelegate
from boomerang.services.notifiers.telegram.delegate import TelegramNotifierDelegate


class TelegramNotifierService:
    name = TELEGRAM_NOTIFIER_SERVICE_NAME
    delegate = TelegramNotifierDelegate()
    sentinel = SentinelDelegate(delegate)
    messenger = Messenger()

    # ------------------------------------------------------------
    # Sentinel mode
    # ------------------------------------------------------------

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

    # ------------------------------------------------------------
    # Notification delivery
    # ------------------------------------------------------------

    @rpc
    async def get_notification_channel_catalog(self):
        catalog = await self.delegate.get_notification_channel_catalog()
        return catalog.model_dump(mode="json", exclude_none=True)

    @on_event("telegram.alerting.notification.requested")
    async def on_notification_requested(self, payload: NotificationRequest):
        await self.delegate.send_notification(payload)

    # ------------------------------------------------------------
    # Degraded status
    # ------------------------------------------------------------

    @degraded_on
    def is_degraded(self):
        return self.delegate.is_degraded_due_to_api_failures()
