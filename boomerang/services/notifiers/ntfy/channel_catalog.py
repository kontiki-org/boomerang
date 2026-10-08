from boomerang_contracts.notification.channel_catalog import (
    ChannelFieldDescriptor,
    NotificationChannelCatalog,
)

from boomerang.core.service_contracts.notifiers.ntfy.service import (
    NTFY_NOTIFIER_SERVICE_NAME,
)


def ntfy_notification_channel_catalog():
    return NotificationChannelCatalog(
        channel_id="ntfy",
        label="ntfy",
        service_name=NTFY_NOTIFIER_SERVICE_NAME,
        summary_field="topic",
        fields=[
            ChannelFieldDescriptor(
                key="topic",
                label="Topic",
                field_type="text",
                required=True,
                placeholder="ntfy topic (example: ops_alerts)",
                display_in_list=True,
            ),
        ],
    )
