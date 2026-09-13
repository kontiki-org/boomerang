# boomerang-contracts

Shared Pydantic models for [Boomerang](https://github.com/kontiki-org/boomerang)
alert producers and notifiers.

Install:

```bash
pip install boomerang-contracts
```

## What you get

| Area | Import | Role |
|------|--------|------|
| Ingest | `NormalizedAlert`, `ALERT_NORMALIZED_EVENT` | Producer → alert-engine |
| Catalogues | `AlertConnectorCatalog`, `NotificationChannelCatalog`, … | RPC catalogue payloads |
| Delivery | `NotificationRequest` | alert-engine → notifier |

```python
from boomerang_contracts import (
    ALERT_NORMALIZED_EVENT,
    NormalizedAlert,
    NotificationRequest,
)
```

Full field reference: [`docs/contracts.md`](https://github.com/kontiki-org/boomerang/blob/main/docs/contracts.md)
in the Boomerang repository.

## License

Apache-2.0
