# Public surface

See also: `PHILOSOPHY.md`.

Connectors may use only the documented public surface below (plus Kontiki runtime APIs).
Do not copy Boomerang contract models into this repository.

## Allowed — alert contracts

```python
from boomerang.core.contracts.alert import (
    ALERT_NORMALIZED_EVENT,
    NormalizedAlert,
    AlertArea,
    AlertConnectorCatalog,
    AlertCategoryCatalog,
    AlertEventTypeCatalog,
    AlertCriterionDescriptor,
)
```

Equivalents: `boomerang.core.contracts.alert.normalized` / `.catalog`.

## Allowed — test helpers (monorepo dogfooding)

```python
from boomerang.testing import (
    start_kontiki_subprocess,  # optional; this starter uses a local wrapper
    write_temp_config,
    safe_unlink,
    # NotificationPublisherMock — only for event-driven connectors that inject bus events
)
```

Kontiki testing: `MockService`, `MockServiceManager`, `MockServiceRunner`.

## Allowed — Kontiki

`Messenger`, `@rpc`, `@task`, `@on_event`, `ServiceDelegate`, `kontiki.runner.cli`, configuration helpers such as `get_parameter` when needed.

## Forbidden

- `boomerang.services.*` (including other alert connectors)
- other connectors’ test steps or mocks
- private / undocumented Boomerang helpers
- duplicating `NormalizedAlert` or catalog models locally

Reading official connectors (`earthquake`, `kontiki_registry`) as **reference** is fine; importing them is not.

## Missing public API

If a Boomerang import outside this surface seems required:

1. **Stop** generation.
2. **Explain** why it is needed.
3. **Propose** extending Boomerang’s public surface (contract, exported test helper, or package).

Do not silently add the dependency. The Starter Kit is also a probe for missing public APIs.
