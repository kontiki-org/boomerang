import logging

from kontiki.messaging import on_event
from kontiki.testing import MockService
from kontiki.web import http


class AlertNormalizedEventCatcher(MockService):
    name = "alert-normalized-event-catcher"

    @on_event("alert.normalized")
    async def on_alert_normalized(self, payload):
        self.event_manager.store_event(
            {"event_type": "alert.normalized", "payload": payload}
        )


class UsgsFeedMock(MockService):
    name = "usgs-feed-mock"

    @http("/feeds/test.geojson", "GET", version="v1")
    async def test_feed(self, request):
        logging.info("Mocking USGS feed")
        _ = request
        return self.http_manager.get_response()
