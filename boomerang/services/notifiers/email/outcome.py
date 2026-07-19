"""HTTP/RPC outcome types for EmailNotifier (structure only)."""

from typing import Any

from pydantic import BaseModel, Field


class OutboundEvent(BaseModel):
    event_type: str
    payload: dict[str, Any]


class EntrypointOutcome(BaseModel):
    http_response: dict[str, Any]
    http_status: int | None = None
    events: list[OutboundEvent] = Field(default_factory=list)
