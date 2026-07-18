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
    recipient_id: str
    endpoint_key: str
    message: NotificationMessage


class NotificationError(BaseModel):
    type: str
    message: str


class NotificationOutcome(BaseModel):
    status: str
    channel: str | None = None
    message: NotificationMessage | None = None
    error: NotificationError | None = None
    request: Any | None = None
