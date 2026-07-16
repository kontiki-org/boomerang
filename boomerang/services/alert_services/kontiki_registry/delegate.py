import logging

from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang.core.contracts.alert_catalog import AlertConnectorCatalog
from boomerang.services.alert_services.kontiki_registry.alert_mapping import (
    registry_event_to_normalized_alert,
)
from boomerang.services.alert_services.kontiki_registry.catalog import (
    REGISTRY_CATEGORY,
    build_alert_subscription_catalog,
)


class KontikiRegistryAlertDelegate(ServiceDelegate):
    async def setup(self) -> None:
        config = self.container.config
        self._category = get_parameter(
            config, "app.kontiki_registry.category", REGISTRY_CATEGORY
        )
        ttl_raw = get_parameter(config, "app.kontiki_registry.alert_ttl_hours", None)
        self._ttl_hours = float(ttl_raw) if ttl_raw is not None else None
        logging.info(
            "KontikiRegistryAlertDelegate configured category=%s ttl_hours=%s",
            self._category,
            self._ttl_hours,
        )

    def get_alert_subscription_catalog(self) -> AlertConnectorCatalog:
        return build_alert_subscription_catalog(category=self._category)

    def build_normalized_alert(self, registry_event_type: str, payload: object):
        if not isinstance(payload, dict):
            logging.warning(
                "Ignoring registry event %s with non-dict payload: %r",
                registry_event_type,
                payload,
            )
            return None
        alert = registry_event_to_normalized_alert(
            registry_event_type,
            payload,
            category=self._category,
            ttl_hours=self._ttl_hours,
        )
        if alert is None:
            logging.warning(
                "Ignoring unsupported or invalid registry event %s payload=%s",
                registry_event_type,
                payload,
            )
        return alert
