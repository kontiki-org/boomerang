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
            channels = row.get("channels") or []
            endpoint_keys = row.get("endpoint_keys") or []
            if len(channels) != len(endpoint_keys):
                continue
            recipient_id = row["recipient_id"]
            for channel, endpoint_key in zip(channels, endpoint_keys):
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
        # Current MVP handles a single-area alert; if multiple areas are provided,
        # only the first one is used for recipient resolution.
        area = payload["areas"][0]
        rpc_args = {
            "area_type": area["type"],
            "area_value": area["value"],
            "severity": payload["severity"],
            "category": payload["category"],
            "event_type": payload["event_type"],
        }

        rpc_client = SubscriptionRpcProxy(messenger)
        recipients = await rpc_client.get_recipients_for_alert(**rpc_args)
        if not recipients:
            return []

        return self._notification_requests_for_recipients(payload, recipients)
