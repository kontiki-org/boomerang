from typing import Any

from pydantic import BaseModel, Field


class NotificationContext(BaseModel):
    kind: str
    data: dict[str, Any] = Field(default_factory=dict)


class NotificationMessage(BaseModel):
    title: str
    body: str
    context: NotificationContext


class NotificationRequest(BaseModel):
    channel: str
    endpoint_key: str
    message: NotificationMessage
