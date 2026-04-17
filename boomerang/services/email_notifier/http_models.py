from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CreateEmailEndpointRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    endpoint_key: str = Field(min_length=1)
    address: str = Field(min_length=1)

    @model_validator(mode="after")
    def _normalize(self) -> "CreateEmailEndpointRequest":
        endpoint_key = (self.endpoint_key or "").strip()
        address = (self.address or "").strip().lower()

        if not endpoint_key or not address:
            raise ValueError("Invalid request payload.")

        self.endpoint_key = endpoint_key
        self.address = address
        return self
