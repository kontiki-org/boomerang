from boomerang.core.contracts.alert_normalized import NormalizedAlert
from boomerang.core.contracts.notification import (
    NotificationContext,
    NotificationMessage,
    NotificationRequest,
)
from boomerang.core.contracts.subscription.service import SubscriptionRpcProxy


class AlertEngineDelegate:
    def _normalized_alert(self, payload) -> NormalizedAlert:
        if isinstance(payload, NormalizedAlert):
            return payload
        return NormalizedAlert.model_validate(payload)

    def _notification_requests_for_recipients(self, alert: NormalizedAlert, recipients):
        message = NotificationMessage(
            title=alert.title,
            body=alert.body,
            context=NotificationContext(
                kind="alert",
                data={
                    "alert_id": alert.alert_id,
                    "category": alert.category,
                    "event_type": alert.event_type,
                    "severity": alert.severity,
                    "attributes": alert.attributes,
                },
            ),
        )
        out = []
        for row in recipients:
            recipient_id = row.get("recipient_id")
            channel = row.get("channel")
            endpoint_key = row.get("endpoint_key")
            if (
                not isinstance(recipient_id, str)
                or not recipient_id
                or not isinstance(channel, str)
                or not channel
                or not isinstance(endpoint_key, str)
                or not endpoint_key
            ):
                continue

            out.append(
                NotificationRequest(
                    channel=channel,
                    recipient_id=recipient_id,
                    endpoint_key=endpoint_key,
                    message=message,
                )
            )
        return out

    async def process_normalized_alert(self, messenger, payload):
        alert = self._normalized_alert(payload)
        recipients = await SubscriptionRpcProxy(messenger).get_recipients_for_alert(
            alert=alert
        )
        if not recipients:
            return []
        return self._notification_requests_for_recipients(alert, recipients)
