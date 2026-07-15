from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

GET_NOTIFICATION_CHANNEL_CATALOG_RPC = "get_notification_channel_catalog"
GET_NOTIFICATION_CHANNELS_CATALOG_RPC = "get_notification_channels_catalog"

ChannelFieldType = Literal["text", "email", "secret", "url", "number", "choice"]


class ChannelFieldChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1)
    value: str = Field(min_length=1)

    @model_validator(mode="after")
    def _normalize(self) -> "ChannelFieldChoice":
        self.label = self.label.strip()
        self.value = self.value.strip()
        if not self.label or not self.value:
            raise ValueError("Invalid catalog field choice.")
        return self


class ChannelFieldDescriptor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    field_type: ChannelFieldType
    required: bool = True
    placeholder: str | None = None
    choices: list[ChannelFieldChoice] | None = None
    display_in_list: bool = False

    @model_validator(mode="after")
    def _normalize(self) -> "ChannelFieldDescriptor":
        self.key = self.key.strip().lower()
        self.label = self.label.strip()
        if not self.key or not self.label:
            raise ValueError("Invalid catalog field descriptor.")
        if self.placeholder is not None:
            self.placeholder = self.placeholder.strip() or None
        if self.field_type != "choice":
            self.choices = None
        return self


class NotificationChannelCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    service_name: str = Field(min_length=1)
    summary_field: str | None = None
    fields: list[ChannelFieldDescriptor] = Field(min_length=1)

    @model_validator(mode="after")
    def _normalize(self) -> "NotificationChannelCatalog":
        self.channel_id = self.channel_id.strip().lower()
        self.label = self.label.strip()
        self.service_name = self.service_name.strip()
        if self.summary_field is not None:
            self.summary_field = self.summary_field.strip().lower() or None
        if (
            not self.channel_id
            or not self.label
            or not self.service_name
            or not self.fields
        ):
            raise ValueError("Invalid notification channel catalog.")
        if self.summary_field is None:
            self.summary_field = self.fields[0].key
        return self


class NotificationChannelsCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channels: list[NotificationChannelCatalog] = Field(default_factory=list)
