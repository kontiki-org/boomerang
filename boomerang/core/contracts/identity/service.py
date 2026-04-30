from kontiki.messaging import RpcProxy


IDENTITY_SERVICE_NAME = "identity-service"

class IdentityRpcProxy(RpcProxy):
    def __init__(self, messenger):
        super().__init__(messenger, IDENTITY_SERVICE_NAME)
