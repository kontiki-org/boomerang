from kontiki.messaging import on_event, rpc
from kontiki.testing import MockService


class AlertNormalizedEventCatcher(MockService):
    name = "alert-normalized-event-catcher"

    @on_event("alert.normalized")
    async def on_alert_normalized(self, payload):
        self.event_manager.store_event(
            {"event_type": "alert.normalized", "payload": payload}
        )


class ServiceRegistryMock(MockService):
    """Sole ServiceRegistry on the bus when using run-dev-platform-no-registry.

    Kontiki RPC handlers receive the ServiceContainer as self, so snapshot state
    lives on the service instance and is read via self.service_instance.
    """

    name = "ServiceRegistry"

    def __init__(self):
        self.services_snapshot = {}

    def set_services(self, services):
        self.services_snapshot = services if services is not None else {}

    @rpc
    async def get_services(self, status=None):
        _ = status
        return self.service_instance.services_snapshot
