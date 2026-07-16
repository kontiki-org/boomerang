from datetime import datetime, timezone

from kontiki.delegate import ServiceDelegate

from boomerang.core.contracts.alert_catalog import AlertConnectorCatalog
from boomerang.core.contracts.alert_normalized import NormalizedAlert
from connector import SERVICE_NAME
from connector.catalog import DEMO_CATEGORY, DEMO_EVENT_TYPE, build_alert_subscription_catalog


class ConnectorDelegate(ServiceDelegate):
    def get_alert_subscription_catalog(self) -> AlertConnectorCatalog:
        return build_alert_subscription_catalog()

    def build_demo_alert(self) -> NormalizedAlert:
        now = datetime.now(timezone.utc)
        return NormalizedAlert(
            alert_id="demo-starter-1",
            source=SERVICE_NAME,
            category=DEMO_CATEGORY,
            event_type=DEMO_EVENT_TYPE,
            severity="low",
            occurred_at=now,
            title="Starter demo alert",
            body="Pedagogical alert from the Boomerang alert connector starter.",
            areas=[],
            attributes={"label": "starter-demo"},
        )
