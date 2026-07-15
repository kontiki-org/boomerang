from kontiki.messaging import RpcProxy

TELEGRAM_NOTIFIER_SERVICE_NAME = "telegram-notifier-service"


class TelegramNotifierRpcProxy(RpcProxy):
    def __init__(self, messenger):
        super().__init__(messenger, TELEGRAM_NOTIFIER_SERVICE_NAME)
