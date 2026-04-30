from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RequestAuthCodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str

    @model_validator(mode="after")
    def _normalize(self) -> "RequestAuthCodeRequest":
        email = self.email.strip().lower()
        if not email:
            raise ValueError("Invalid request payload.")
        self.email = email
        return self


class ConsumeAuthCodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=6, max_length=6)

    @model_validator(mode="after")
    def _normalize(self) -> "ConsumeAuthCodeRequest":
        code = self.code.strip()
        if not code:
            raise ValueError("Invalid request payload.")
        self.code = code
        return self
