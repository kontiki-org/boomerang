from kontiki.messaging import rpc
from kontiki.testing import MockService


class IdentityServiceMock(MockService):
    name = "identity-service"

    @rpc
    async def verify_session(self, access_token: str):
        self.remote_call_manager.store_call_args(access_token)
        return self.remote_call_manager.get_return_value()

