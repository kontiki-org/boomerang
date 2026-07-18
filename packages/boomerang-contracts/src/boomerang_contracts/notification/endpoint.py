from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CreateEndpointRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    endpoint_key: str = Field(min_length=1)
    fields: dict[str, str] = Field(min_length=1)

    @model_validator(mode="after")
    def _normalize(self) -> "CreateEndpointRequest":
        endpoint_key = (self.endpoint_key or "").strip()
        if not endpoint_key:
            raise ValueError("Invalid request payload.")
        normalized_fields: dict[str, str] = {}
        for key, value in self.fields.items():
            normalized_key = (key or "").strip().lower()
            normalized_value = (value or "").strip()
            if not normalized_key or not normalized_value:
                raise ValueError("Invalid request payload.")
            normalized_fields[normalized_key] = normalized_value
        if not normalized_fields:
            raise ValueError("Invalid request payload.")
        self.endpoint_key = endpoint_key
        self.fields = normalized_fields
        return self


class CreateChannelEndpointRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel_id: str = Field(min_length=1)
    endpoint_key: str = Field(min_length=1)
    fields: dict[str, str] = Field(min_length=1)

    @model_validator(mode="after")
    def _normalize(self) -> "CreateChannelEndpointRequest":
        channel_id = (self.channel_id or "").strip().lower()
        endpoint_key = (self.endpoint_key or "").strip()
        if not channel_id or not endpoint_key:
            raise ValueError("Invalid request payload.")
        normalized_fields: dict[str, str] = {}
        for key, value in self.fields.items():
            normalized_key = (key or "").strip().lower()
            normalized_value = (value or "").strip()
            if not normalized_key or not normalized_value:
                raise ValueError("Invalid request payload.")
            normalized_fields[normalized_key] = normalized_value
        if not normalized_fields:
            raise ValueError("Invalid request payload.")
        self.channel_id = channel_id
        self.endpoint_key = endpoint_key
        self.fields = normalized_fields
        return self
