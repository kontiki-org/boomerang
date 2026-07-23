from kontiki.testing import MockService
from kontiki.web import http


class TelegramApiMock(MockService):
    name = "telegram-api-mock"

    @http("/bottest-bot-token/sendMessage", "POST", version="v1")
    async def send_message(self, request):
        payload = await request.json()
        self.http_manager.store_request(payload)
        chat_id = (payload.get("chat_id") or "").strip()
        text = (payload.get("text") or "").strip()
        if not chat_id or not text:
            raise RuntimeError("invalid telegram payload")
        try:
            return self.http_manager.get_response()
        except RuntimeError:
            return {"ok": True, "result": {"message_id": 1}}
