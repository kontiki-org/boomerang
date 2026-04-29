from kontiki.messaging import RpcProxy


class IdentityRpcProxy(RpcProxy):
    service_name = "identity-service"

    def __init__(self, messenger):
        super().__init__(messenger, self.service_name)
