from boomerang.core.contracts.notification import (
    NotificationContext,
    NotificationMessage,
    NotificationRequest,
)
from boomerang.core.contracts.subscription.service import SubscriptionRpcProxy


class AlertEngineDelegate:
    def _notification_requests_for_recipients(self, payload, recipients):
        message = NotificationMessage(
            title=payload["headline"],
            body=payload["message"],
            context=NotificationContext(
                kind="alert",
                data={
                    "alert_id": payload["alert_id"],
                    "category": payload["category"],
                    "event_type": payload["event_type"],
                    "severity": payload["severity"],
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
        rpc_args = {"alert": payload}

        rpc_client = SubscriptionRpcProxy(messenger)
        recipients = await rpc_client.get_recipients_for_alert(**rpc_args)
        if not recipients:
            return []

        return self._notification_requests_for_recipients(payload, recipients)
