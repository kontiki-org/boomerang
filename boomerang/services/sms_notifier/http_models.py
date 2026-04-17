from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CreateSmsEndpointRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    endpoint_key: str = Field(min_length=1)
    phone_number: str = Field(min_length=1)

    @model_validator(mode="after")
    def _normalize(self) -> "CreateSmsEndpointRequest":
        endpoint_key = (self.endpoint_key or "").strip()
        phone_number = (self.phone_number or "").strip()
        if not endpoint_key or not phone_number:
            raise ValueError("Invalid request payload.")
        self.endpoint_key = endpoint_key
        self.phone_number = phone_number
        return self

