from kontiki.testing import MockService
from kontiki.web import http


class ZulipServerMock(MockService):
    name = "zulip-server-mock"

    @http("/api/v1/messages", "POST", version="v1")
    async def send_message(self, request):
        form = await request.post()
        payload = {
            "type": form.get("type", ""),
            "to": form.get("to", ""),
            "topic": form.get("topic", ""),
            "content": form.get("content", ""),
        }
        authorization = request.headers.get("Authorization", "")
        self.http_manager.store_request(
            {"authorization": authorization, "body": payload}
        )
        destination = (payload.get("to") or "").strip()
        topic = (payload.get("topic") or "").strip()
        content = (payload.get("content") or "").strip()
        if (
            payload.get("type") != "stream"
            or not destination
            or not topic
            or not content
        ):
            raise RuntimeError("invalid zulip payload")
        return {"result": "success", "id": 1}
