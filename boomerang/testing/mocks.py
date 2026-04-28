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
        channel = "email"
        if isinstance(payload, dict):
            channel = (payload.get("channel") or "email").strip() or "email"
        await self.messenger.publish(
            f"{channel}.alerting.notification.requested", payload
        )

    @rpc
    async def publish_event(self, event_type: str, payload):
        await self.messenger.publish(event_type, payload)


class EmailNotifierServiceMock(MockService):
    name = "email-notifier-service"

    @rpc
    async def ensure_auth_email_endpoint(
        self,
        user_id: str,
        endpoint_key: str,
        address: str,
    ):
        self.remote_call_manager.store_call_args(
            user_id,
            endpoint_key,
            address,
        )
        return self.remote_call_manager.get_return_value()
