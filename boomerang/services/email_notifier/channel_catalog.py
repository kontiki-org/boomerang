from boomerang.core.contracts.email_notifier.service import EMAIL_NOTIFIER_SERVICE_NAME
from boomerang.core.contracts.notification_channel_catalog import (
    ChannelFieldDescriptor,
    NotificationChannelCatalog,
)


def email_notification_channel_catalog() -> NotificationChannelCatalog:
    return NotificationChannelCatalog(
        channel_id="email",
        label="Email",
        service_name=EMAIL_NOTIFIER_SERVICE_NAME,
        summary_field="address",
        fields=[
            ChannelFieldDescriptor(
                key="address",
                label="Destination",
                field_type="email",
                required=True,
                placeholder="email address (example: user@example.org)",
                display_in_list=True,
            ),
        ],
    )
