from kontiki.messaging import RpcProxy


class SubscriptionRpcProxy(RpcProxy):
    service_name = "subscription-service"

    def __init__(self, messenger):
        super().__init__(messenger, self.service_name)
