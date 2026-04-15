from kontiki.messaging import on_event
from kontiki.testing import MockService


class NotificationEventCatcher(MockService):
    name = "notification-event-catcher"

    @on_event("alerting.notification.requested")
    async def on_notification_requested(self, payload):
        self.event_manager.store_event(
            {"event_type": "alerting.notification.requested", "payload": payload}
        )
