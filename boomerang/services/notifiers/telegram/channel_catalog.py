from boomerang_contracts.notification.channel_catalog import (
    ChannelFieldDescriptor,
    NotificationChannelCatalog,
)
from boomerang.core.service_contracts.notifiers.telegram.service import (
    TELEGRAM_NOTIFIER_SERVICE_NAME,
)


def telegram_notification_channel_catalog() -> NotificationChannelCatalog:
    return NotificationChannelCatalog(
        channel_id="telegram",
        label="Telegram",
        service_name=TELEGRAM_NOTIFIER_SERVICE_NAME,
        summary_field="chat_id",
        fields=[
            ChannelFieldDescriptor(
                key="chat_id",
                label="Chat ID",
                field_type="text",
                required=True,
                placeholder="Telegram chat ID (example: 123456789)",
                display_in_list=True,
            ),
        ],
    )
