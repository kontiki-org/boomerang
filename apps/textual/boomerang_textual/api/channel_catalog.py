from __future__ import annotations

from dataclasses import dataclass, field

from boomerang.core.contracts.notification_channel_catalog import (
    ChannelFieldDescriptor,
    NotificationChannelCatalog,
    NotificationChannelsCatalog,
)


@dataclass
class ChannelCatalogIndex:
    channels: list[tuple[str, str]] = field(default_factory=list)
    fields_by_channel: dict[str, list[ChannelFieldDescriptor]] = field(
        default_factory=dict
    )
    channel_by_id: dict[str, NotificationChannelCatalog] = field(default_factory=dict)


def channel_catalog_from_rpc(raw) -> NotificationChannelsCatalog:
    if isinstance(raw, NotificationChannelsCatalog):
        return raw
    return NotificationChannelsCatalog.model_validate(raw)


def build_channel_catalog_index(
    catalog: NotificationChannelsCatalog,
) -> ChannelCatalogIndex:
    index = ChannelCatalogIndex()
    for channel in catalog.channels:
        index.channels.append((channel.label, channel.channel_id))
        index.fields_by_channel[channel.channel_id] = list(channel.fields)
        index.channel_by_id[channel.channel_id] = channel
    index.channels.sort(key=lambda item: item[0])
    return index
