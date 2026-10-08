from kontiki.testing import MockService
from kontiki.web import http


class NtfyServerMock(MockService):
    name = "ntfy-server-mock"

    @http("/", "POST", version="v1")
    async def publish(self, request):
        payload = await request.json()
        authorization = request.headers.get("Authorization", "")
        self.http_manager.store_request(
            {"authorization": authorization, "body": payload}
        )
        topic = (payload.get("topic") or "").strip()
        message = (payload.get("message") or "").strip()
        if not topic or not message:
            raise RuntimeError("invalid ntfy payload")
        return {"id": "1"}
