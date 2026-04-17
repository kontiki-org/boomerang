from kontiki.messaging import Messenger, rpc
from kontiki.testing import MockService


class IdentityServiceMock(MockService):
    name = "identity-service"

    @rpc
    async def verify_session(self, access_token: str):
        self.remote_call_manager.store_call_args(access_token)
        return self.remote_call_manager.get_return_value()


class NotificationPublisherMock(MockService):
    name = "notification-publisher"
    messenger = Messenger()

    @rpc
    async def publish_notification_requested(self, payload):
        await self.messenger.publish("alerting.notification.requested", payload)
