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
    async def verify_session(container, access_token: str):
        # Kontiki passes ServiceContainer as first argument for RPC handlers.
        service = container.service_instance
        service.store_call_args(access_token)
        return service.get_return_value()
