from kontiki.messaging import RpcClientError, RpcTimeoutError


def rpc_error_message(exc: Exception) -> str:
    if isinstance(exc, (RpcClientError, RpcTimeoutError)):
        if exc.code == "AUTH_ERROR":
            return "Session expired or invalid. Please sign in again."
        return exc.message or "Request rejected."
    return str(exc)
