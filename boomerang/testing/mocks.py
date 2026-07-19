from kontiki.messaging import Messenger, rpc
from kontiki.testing import MockService


class NotificationPublisherMock(MockService):
    name = "notification-publisher"
    messenger = Messenger()

    @rpc
    async def publish_notification_requested(self, payload):
        channel = "email"
        if isinstance(payload, dict):
            channel = (payload.get("channel") or "email").strip() or "email"
        await self.messenger.publish(
            f"{channel}.alerting.notification.requested", payload
        )

    @rpc
    async def publish_event(self, event_type: str, payload):
        await self.messenger.publish(event_type, payload)
