import re

from boomerang_contracts.exceptions import ValidationError
from boomerang_contracts.notification.validation import validate_endpoint_fields

_TOPIC_RE = re.compile(r"[-_A-Za-z0-9]{1,64}")


class ConfiguredEndpointStore:
    def __init__(self, endpoints):
        self._endpoints = endpoints

    def __len__(self):
        return len(self._endpoints)

    def get(self, endpoint_id):
        key = (endpoint_id or "").strip()
        if not key:
            return None
        return self._endpoints.get(key)


def load_configured_endpoints(raw, catalog):
    if raw is None:
        return ConfiguredEndpointStore({})
    if not isinstance(raw, dict):
        raise RuntimeError("Invalid app.endpoints configuration.")

    endpoints = {}
    for endpoint_id, fields_raw in raw.items():
        key = str(endpoint_id).strip()
        if not key:
            raise RuntimeError(
                "Invalid app.endpoints configuration: empty endpoint_id."
            )
        if not isinstance(fields_raw, dict):
            raise RuntimeError(
                f"Invalid app.endpoints configuration for endpoint {key!r}."
            )
        try:
            string_fields = {
                str(field_key): str(value) for field_key, value in fields_raw.items()
            }
            fields = validate_endpoint_fields(catalog, string_fields)
        except ValidationError as exc:
            raise RuntimeError(
                f"Invalid app.endpoints configuration for endpoint {key!r}."
            ) from exc
        topic = fields.get("topic", "")
        if not _TOPIC_RE.fullmatch(topic):
            raise RuntimeError(
                f"Invalid app.endpoints configuration for endpoint {key!r}:"
                " invalid topic."
            )
        endpoints[key] = fields
    return ConfiguredEndpointStore(endpoints)
