import logging

from boomerang_contracts.alert.catalog import (
    AlertConnectorCatalog,
    AlertSubscriptionCatalog,
)
from boomerang_contracts.notification.channel_catalog import (
    NotificationChannelCatalog,
    NotificationChannelsCatalog,
)
from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate
from kontiki.messaging import RpcProxy

from boomerang.services.subscription.configured_subscriptions import (
    load_configured_subscriptions,
)


def _connector_catalog_from_rpc_result(raw) -> AlertConnectorCatalog:
    if isinstance(raw, AlertConnectorCatalog):
        return raw
    return AlertConnectorCatalog.model_validate(raw)


def _channel_catalog_from_rpc_result(raw) -> NotificationChannelCatalog:
    if isinstance(raw, NotificationChannelCatalog):
        return raw
    return NotificationChannelCatalog.model_validate(raw)


class SubscriptionDelegate(ServiceDelegate):
    async def setup(self):
        configured_connectors = get_parameter(
            self.container.config, "app.alert_connectors", []
        )
        self._alert_connectors = []
        if isinstance(configured_connectors, list):
            for entry in configured_connectors:
                if isinstance(entry, str):
                    name = entry.strip()
                    if name:
                        self._alert_connectors.append(name)
        configured_notification_channels = get_parameter(
            self.container.config,
            "app.notification_channels",
            [],
        )
        self._notification_channels = []
        if isinstance(configured_notification_channels, list):
            for entry in configured_notification_channels:
                if isinstance(entry, str):
                    name = entry.strip()
                    if name:
                        self._notification_channels.append(name)
        configured_subscriptions = get_parameter(
            self.container.config,
            "app.subscriptions",
            None,
        )
        self._configured_subscriptions = load_configured_subscriptions(
            configured_subscriptions
        )
        logging.info(
            "SubscriptionDelegate configured (connectors=%s"
            " notification_channels=%s configured_subscriptions=%s)",
            self._alert_connectors,
            self._notification_channels,
            len(self._configured_subscriptions),
        )

    async def get_alert_subscription_catalog(
        self, messenger
    ) -> AlertSubscriptionCatalog:
        sources: list[AlertConnectorCatalog] = []
        for service_name in self._alert_connectors:
            proxy = RpcProxy(messenger, service_name)
            raw = await proxy.get_alert_subscription_catalog()
            sources.append(_connector_catalog_from_rpc_result(raw))
        return AlertSubscriptionCatalog(sources=sources)

    async def get_notification_channels_catalog(
        self,
        messenger,
    ) -> NotificationChannelsCatalog:
        channels: list[NotificationChannelCatalog] = []
        for service_name in self._notification_channels:
            proxy = RpcProxy(messenger, service_name)
            raw = await proxy.get_notification_channel_catalog()
            channels.append(_channel_catalog_from_rpc_result(raw))
        return NotificationChannelsCatalog(channels=channels)

    async def get_recipients_for_alert(self, alert_payload):
        return self._configured_subscriptions.get_recipients_for_alert(alert_payload)
