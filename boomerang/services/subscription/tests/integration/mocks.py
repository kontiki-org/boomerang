from kontiki.messaging import on_event, rpc
from kontiki.testing import MockService


class NotificationEventCatcher(MockService):
    name = "notification-event-catcher"

    @on_event("alerting.notification.requested")
    async def on_notification_requested(self, payload):
        self.event_manager.store_event(
            {"event_type": "alerting.notification.requested", "payload": payload}
        )


class IdentityServiceMock(MockService):
    name = "identity-service"

    @rpc
    async def verify_session(self,access_token: str):
        self.remote_call_manager.store_call_args(access_token)
        return self.remote_call_manager.get_return_value()
