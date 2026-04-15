from typing import Any

from pydantic import BaseModel, Field

from boomerang.core.contracts.notification import NotificationRequest


class OutboundEvent(BaseModel):
    event_type: str
    payload: NotificationRequest


class EntrypointOutcome(BaseModel):
    http_response: dict[str, Any]
    events: list[OutboundEvent] = Field(default_factory=list)
