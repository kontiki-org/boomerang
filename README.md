<img src="./assets/boomerang_logo.png" width="500">

Boomerang is an alerting engine on [Kontiki](https://github.com/kontiki-org/kontiki).
A producer emits a `NormalizedAlert`. Subscription and the alert engine match YAML rules and emit a `NotificationRequest` per channel endpoint. A notifier delivers it.

```text
Producer → NormalizedAlert → subscription + alert-engine → NotificationRequest → notifier
```

Kontiki 2, RabbitMQ ≥ 4.3. Who gets notified is `app.subscriptions` and the notifier’s `app.endpoints`.

## Services

## Services

| Service | Image |
|---------|--------|
| [Subscription](boomerang/services/subscription/README.md) | `ghcr.io/kontiki-org/boomerang-subscription:1.0.0` |
| [Alert engine](boomerang/services/alert_engine/README.md) | `ghcr.io/kontiki-org/boomerang-alert-engine:1.0.0` |
| [Email](boomerang/services/notifiers/email/README.md) | `ghcr.io/kontiki-org/boomerang-email-notifier:1.0.0` |
| [Telegram](boomerang/services/notifiers/telegram/README.md) | `ghcr.io/kontiki-org/boomerang-telegram-notifier:1.0.0` |
| [ntfy](boomerang/services/notifiers/ntfy/README.md) | `ghcr.io/kontiki-org/boomerang-ntfy-notifier:1.0.0` |

## Contracts

Producers and notifiers share [`boomerang-contracts`](packages/boomerang-contracts/README.md) (`2.0.0`):

```bash
pip install boomerang-contracts
```

## Demo

USGS quakes, normalized, then Telegram and email (MailHog). Rules: `stack/subscription.demo.yaml` (`magnitude >= 2` → `telegram.alerts` and `email.inbox`).

```bash
cp stack/notifiers/telegram_bot_token.yaml.example stack/notifiers/telegram_bot_token.yaml
```

Set `app.telegram.bot_token`, and `app.endpoints.alerts.chat_id` in `stack/notifiers/telegram.yaml`. Then:

```bash
make stack-up-demo
```

MailHog: http://127.0.0.1:8025. Stop with `make stack-down`.

<p align="center">
  <img src="./assets/telegram-earthquake-alert.png" alt="Telegram notification from the earthquake demo" width="420">
</p>

## Docs

[Features](docs/features.md) · [Contracts](docs/contracts.md) · [Configuration](docs/configuration.md) · [Example YAML](docs/boomerang-config.example.yaml) · [Contributing](CONTRIBUTING.md) · [License](LICENSE) Apache-2.0
