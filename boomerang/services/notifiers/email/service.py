from kontiki.messaging import Messenger, on_event, rpc
from kontiki.registry import degraded_on

from boomerang.core.service_contracts.notifiers.email.service import EMAIL_NOTIFIER_SERVICE_NAME
from boomerang_contracts.notification.message import (
    NotificationError,
    NotificationOutcome,
    NotificationRequest,
)
from boomerang.services.notifiers.email.delegate import EmailNotifierDelegate


class EmailNotifierService:
    name = EMAIL_NOTIFIER_SERVICE_NAME
    delegate = EmailNotifierDelegate()
    messenger = Messenger()

    @rpc
    async def get_notification_channel_catalog(self):
        catalog = await self.delegate.get_notification_channel_catalog()
        return catalog.model_dump(mode="json", exclude_none=True)

    @on_event("email.alerting.notification.requested")
    async def on_notification_requested(self, payload):
        request = (
            payload
            if isinstance(payload, NotificationRequest)
            else NotificationRequest.model_validate(payload)
        )
        try:
            await self.delegate.send_notification_email(request)
        except Exception as exc:
            await self.messenger.publish(
                "alerting.notification.failed",
                NotificationOutcome(
                    status="failed",
                    channel=request.channel,
                    message=request.message,
                    error=NotificationError(
                        type="delivery_error",
                        message=str(exc),
                    ),
                ),
            )
            return
        await self.messenger.publish(
            "alerting.notification.delivered",
            NotificationOutcome(
                status="delivered",
                channel=request.channel,
                message=request.message,
            ),
        )

    @degraded_on
    def is_degraded(self):
        return self.delegate.is_degraded_due_to_smtp_failures()
