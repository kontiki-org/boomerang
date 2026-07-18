from boomerang.core.service_contracts.alert_services.earthquake import (
    EARTHQUAKE_FEED_SERVICE_NAME,
    EarthquakeFeedRpcProxy,
)
from boomerang.core.service_contracts.alert_services.kontiki_registry import (
    KONTIKI_REGISTRY_ALERT_SERVICE_NAME,
    KontikiRegistryAlertRpcProxy,
)

__all__ = [
    "EARTHQUAKE_FEED_SERVICE_NAME",
    "EarthquakeFeedRpcProxy",
    "KONTIKI_REGISTRY_ALERT_SERVICE_NAME",
    "KontikiRegistryAlertRpcProxy",
]
