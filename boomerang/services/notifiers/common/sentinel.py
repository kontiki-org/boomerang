from kontiki.configuration.parameter import get_parameter
from kontiki.delegate import ServiceDelegate

from boomerang.services.notifiers.common.watchdog import accept_heartbeat, load_watchdog


class SentinelDelegate(ServiceDelegate):
    def __init__(self, notifier):
        self._notifier = notifier
        self._engine = None
        super().__init__()

    async def setup(self):
        raw = get_parameter(self.container.config, "app.sentinel", None)
        if raw is None:
            return
        self._engine = load_watchdog(raw, self._notifier.configured_endpoints)

    async def start(self):
        if self._engine is None:
            return
        self._engine.start(self._notifier.channel_id, self._notifier.send_notification)

    async def stop(self):
        if self._engine is None:
            return
        await self._engine.stop()

    def observe_heartbeat(self, request, name):
        accept_heartbeat(self._engine, request.headers, name)
