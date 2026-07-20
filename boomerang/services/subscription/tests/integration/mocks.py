from boomerang_contracts.alert.catalog import (
    AlertCategoryCatalog,
    AlertConnectorCatalog,
    AlertCriterionDescriptor,
    AlertEventTypeCatalog,
)
from kontiki.messaging import on_event, rpc
from kontiki.testing import MockService

from boomerang.core.service_contracts.alert_services.earthquake import (
    EARTHQUAKE_FEED_SERVICE_NAME,
)

WEATHER_ALERT_SERVICE_NAME = "weather-alert-service"


def _earthquake_connector_catalog():
    return AlertConnectorCatalog(
        source_id=EARTHQUAKE_FEED_SERVICE_NAME,
        categories=[
            AlertCategoryCatalog(
                category="natural.earthquake",
                label="Earthquake",
                event_types=[
                    AlertEventTypeCatalog(
                        event_type="earthquake",
                        label="Earthquake",
                        criteria=[
                            AlertCriterionDescriptor(
                                key="magnitude",
                                label="Minimum magnitude",
                                operators=["gte"],
                                value_kind="number",
                            ),
                        ],
                    )
                ],
            )
        ],
    )


def _weather_connector_catalog():
    return AlertConnectorCatalog(
        source_id=WEATHER_ALERT_SERVICE_NAME,
        categories=[
            AlertCategoryCatalog(
                category="weather.alert",
                label="Weather",
                event_types=[
                    AlertEventTypeCatalog(
                        event_type="wind",
                        label="Wind",
                        criteria=[
                            AlertCriterionDescriptor(
                                key="min_severity",
                                label="Minimum severity",
                                operators=["gte"],
                                value_kind="string",
                            ),
                        ],
                    )
                ],
            )
        ],
    )


class NotificationEventCatcher(MockService):
    name = "notification-event-catcher"

    @on_event("email.alerting.notification.requested")
    async def on_notification_requested(self, payload):
        self.event_manager.store_event(
            {
                "event_type": "email.alerting.notification.requested",
                "payload": payload,
            }
        )


class EarthquakeFeedCatalogMock(MockService):
    name = EARTHQUAKE_FEED_SERVICE_NAME

    @rpc
    async def get_alert_subscription_catalog(self):
        return _earthquake_connector_catalog()


class WeatherAlertCatalogMock(MockService):
    name = WEATHER_ALERT_SERVICE_NAME

    @rpc
    async def get_alert_subscription_catalog(self):
        return _weather_connector_catalog()
