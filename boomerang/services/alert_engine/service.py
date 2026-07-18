from aiohttp.web import HTTPUnprocessableEntity
from kontiki.messaging import Messenger, on_event
from kontiki.web import http

from boomerang_contracts.alert.normalized import ALERT_NORMALIZED_EVENT
from boomerang.core.exceptions import AuthError, ValidationError
from boomerang.services.alert_engine.delegate import AlertEngineDelegate


class AlertEngineService:
    name = "alert-engine-service"
    delegate = AlertEngineDelegate()
    messenger = Messenger()
    http_error_handlers = {
        ValidationError: (422, ValidationError.message),
        HTTPUnprocessableEntity: (422, ValidationError.message),
        AuthError: (401, AuthError.message),
    }

    async def handle_normalized_alert(self, payload):
        requests = await self.delegate.process_normalized_alert(self.messenger, payload)
        if not requests:
            return
        for request in requests:
            event_type = f"{request.channel}.alerting.notification.requested"
            await self.messenger.publish(event_type, request)

    # HTTP API

    @http("/alerts", "POST", status_code=202, errors=[ValidationError, AuthError])
    async def post_alert_http(self, request):
        self.delegate.require_http_auth(request)
        alert = await self.delegate.parse_normalized_alert(request)
        await self.handle_normalized_alert(alert)
        return {"alert_id": alert.alert_id}

    # AMQP API

    @on_event(ALERT_NORMALIZED_EVENT)
    async def on_alert_normalized(self, payload):
        await self.handle_normalized_alert(payload)
