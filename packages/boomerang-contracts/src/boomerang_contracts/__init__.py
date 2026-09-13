"""Shared Boomerang contracts for alert connectors and notifiers."""

from boomerang_contracts.alert import (
    ALERT_NORMALIZED_EVENT,
    GET_ALERT_SUBSCRIPTION_CATALOG_RPC,
    AlertArea,
    AlertCategoryCatalog,
    AlertConnectorCatalog,
    AlertCriterionDescriptor,
    AlertEventTypeCatalog,
    AlertSubscriptionCatalog,
    NormalizedAlert,
)
from boomerang_contracts.exceptions import ValidationError
from boomerang_contracts.notification import (
    GET_NOTIFICATION_CHANNEL_CATALOG_RPC,
    GET_NOTIFICATION_CHANNELS_CATALOG_RPC,
    ChannelFieldChoice,
    ChannelFieldDescriptor,
    NotificationChannelCatalog,
    NotificationChannelsCatalog,
    NotificationContext,
    NotificationMessage,
    NotificationRequest,
    endpoint_display,
    validate_endpoint_fields,
)

__all__ = [
    "ALERT_NORMALIZED_EVENT",
    "AlertArea",
    "AlertCategoryCatalog",
    "AlertConnectorCatalog",
    "AlertCriterionDescriptor",
    "AlertEventTypeCatalog",
    "AlertSubscriptionCatalog",
    "ChannelFieldChoice",
    "ChannelFieldDescriptor",
    "GET_ALERT_SUBSCRIPTION_CATALOG_RPC",
    "GET_NOTIFICATION_CHANNEL_CATALOG_RPC",
    "GET_NOTIFICATION_CHANNELS_CATALOG_RPC",
    "NormalizedAlert",
    "NotificationChannelCatalog",
    "NotificationChannelsCatalog",
    "NotificationContext",
    "NotificationMessage",
    "NotificationRequest",
    "ValidationError",
    "endpoint_display",
    "validate_endpoint_fields",
]
