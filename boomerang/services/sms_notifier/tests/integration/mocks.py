from kontiki.messaging import on_event
from kontiki.testing import MockService
from kontiki.web import http


class NotificationOutcomeCatcher(MockService):
    name = "notification-outcome-catcher"

    @on_event("alerting.notification.delivered")
    async def on_notification_delivered(self, payload):
        self.event_manager.store_event(
            {"event_type": "alerting.notification.delivered", "payload": payload}
        )

    @on_event("alerting.notification.failed")
    async def on_notification_failed(self, payload):
        self.event_manager.store_event(
            {"event_type": "alerting.notification.failed", "payload": payload}
        )


class SmsProviderMock(MockService):
    name = "sms-provider-service"

    @http("/sms/send", "POST", version="v1")
    async def send_sms(self, request):
        payload = await request.json()
        self.http_manager.store_request(payload)
        to = (payload.get("to") or "").strip()
        body = (payload.get("body") or "").strip()
        if not to or not body:
            raise RuntimeError("invalid sms payload")
        try:
            return self.http_manager.get_response()
        except RuntimeError:
            return {"status": "ok"}

