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


class TelegramApiMock(MockService):
    name = "telegram-api-mock"

    @http("/bottest-bot-token/sendMessage", "POST", version="v1")
    async def send_message(self, request):
        payload = await request.json()
        self.http_manager.store_request(payload)
        chat_id = (payload.get("chat_id") or "").strip()
        text = (payload.get("text") or "").strip()
        if not chat_id or not text:
            raise RuntimeError("invalid telegram payload")
        try:
            return self.http_manager.get_response()
        except RuntimeError:
            return {"ok": True, "result": {"message_id": 1}}
