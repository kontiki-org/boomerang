from kontiki.messaging import on_event
from kontiki.testing import MockService


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
