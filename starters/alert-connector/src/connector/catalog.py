from connector import SERVICE_NAME

from boomerang_contracts.alert.catalog import (
    AlertCategoryCatalog,
    AlertConnectorCatalog,
    AlertCriterionDescriptor,
    AlertEventTypeCatalog,
)

DEMO_CATEGORY = "demo.starter"
DEMO_EVENT_TYPE = "demo_alert"


def build_alert_subscription_catalog() -> AlertConnectorCatalog:
    return AlertConnectorCatalog(
        source_id=SERVICE_NAME,
        categories=[
            AlertCategoryCatalog(
                category=DEMO_CATEGORY,
                label="Starter demo",
                event_types=[
                    AlertEventTypeCatalog(
                        event_type=DEMO_EVENT_TYPE,
                        label="Demo alert",
                        criteria=[
                            AlertCriterionDescriptor(
                                key="label",
                                label="Label",
                                operators=["eq", "contains"],
                                value_kind="string",
                            ),
                        ],
                    )
                ],
            )
        ],
    )
