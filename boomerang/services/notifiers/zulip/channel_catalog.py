from boomerang_contracts.notification.channel_catalog import (
    ChannelFieldDescriptor,
    NotificationChannelCatalog,
)

from boomerang.core.service_contracts.notifiers.zulip.service import (
    ZULIP_NOTIFIER_SERVICE_NAME,
)


def zulip_notification_channel_catalog():
    return NotificationChannelCatalog(
        channel_id="zulip",
        label="Zulip",
        service_name=ZULIP_NOTIFIER_SERVICE_NAME,
        summary_field="channel",
        fields=[
            ChannelFieldDescriptor(
                key="channel",
                label="Channel",
                field_type="text",
                required=True,
                placeholder="Zulip channel (example: ops)",
                display_in_list=True,
            ),
            ChannelFieldDescriptor(
                key="topic",
                label="Topic",
                field_type="text",
                required=True,
                placeholder="Zulip topic (example: alerts)",
                display_in_list=True,
            ),
        ],
    )
