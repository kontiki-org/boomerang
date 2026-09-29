import logging

from boomerang_contracts.alert.catalog import (
    AlertConnectorCatalog,
    AlertSubscriptionCatalog,
)
from boomerang_contracts.notification.channel_catalog import (
    NotificationChannelCatalog,
    NotificationChannelsCatalog,
)
from kontiki.delegate import ServiceDelegate
from kontiki.messaging import RpcProxy


class CatalogNotConfigured(Exception):
    code = "CATALOG_NOT_CONFIGURED"

    def __init__(self, message):
        self.message = message
        super().__init__(message)


class CatalogDelegate(ServiceDelegate):
    async def setup(self):
        self._alert_connectors = self._configured_service_names("alert_connectors")
        self._notification_channels = self._configured_service_names(
            "notification_channels"
        )
        logging.info(
            "CatalogDelegate configured (connectors=%s notification_channels=%s)",
            self._alert_connectors,
            self._notification_channels,
        )

    async def get_alert_subscription_catalog(self, messenger):
        sources = []
        for service_name in self._require_configured_names(
            self._alert_connectors, "alert_connectors"
        ):
            proxy = RpcProxy(messenger, service_name)
            raw = await proxy.get_alert_subscription_catalog()
            if not isinstance(raw, AlertConnectorCatalog):
                raw = AlertConnectorCatalog.model_validate(raw)
            sources.append(raw)
        return AlertSubscriptionCatalog(sources=sources)

    async def get_notification_channels_catalog(self, messenger):
        channels = []
        for service_name in self._require_configured_names(
            self._notification_channels, "notification_channels"
        ):
            proxy = RpcProxy(messenger, service_name)
            raw = await proxy.get_notification_channel_catalog()
            if not isinstance(raw, NotificationChannelCatalog):
                raw = NotificationChannelCatalog.model_validate(raw)
            channels.append(raw)
        return NotificationChannelsCatalog(channels=channels)

    def _configured_service_names(self, key):
        app = self.container.config.get("app")
        if not isinstance(app, dict) or key not in app or app[key] is None:
            return None
        names = []
        raw = app[key]
        if isinstance(raw, list):
            for entry in raw:
                if isinstance(entry, str):
                    name = entry.strip()
                    if name:
                        names.append(name)
        return names

    @staticmethod
    def _require_configured_names(names, parameter):
        if names is not None:
            return names
        message = "app.%s is not configured" % parameter
        logging.warning(message)
        raise CatalogNotConfigured(message)
