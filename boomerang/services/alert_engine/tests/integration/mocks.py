from kontiki.messaging import on_event, rpc
from kontiki.testing import MockService


class SubscriptionServiceMock(MockService):
    name = "subscription-service"

    @rpc
    async def get_recipients_for_alert(self, alert):
        self.remote_call_manager.store_call_args(alert)
        return self.remote_call_manager.get_return_value()


class NotificationDispatchEventCatcher(MockService):
    name = "notification-dispatch-event-catcher"

    @on_event("email.alerting.notification.requested")
    async def on_email_notification_requested(self, payload):
        self.event_manager.store_event(
            {
                "event_type": "email.alerting.notification.requested",
                "payload": payload,
            }
        )

    @on_event("sms.alerting.notification.requested")
    async def on_sms_notification_requested(self, payload):
        self.event_manager.store_event(
            {
                "event_type": "sms.alerting.notification.requested",
                "payload": payload,
            }
        )
