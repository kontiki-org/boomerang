from kontiki.delegate import ServiceDelegate
from kontiki.messaging import Messenger, on_event, rpc


class AppDelegate(ServiceDelegate):
    async def setup(self):
        # init from self.container.config
        pass

    async def do_something(self, x: int) -> int:
        return x * 2


class AppService:
    name = "app-service"  # override as needed
    delegate = AppDelegate()
    messenger = Messenger()

    @rpc
    async def compute(self, x: int) -> int:
        return await self.delegate.do_something(x)

    @on_event("app.event")
    async def on_event(self, payload):
        # handle event
        pass
