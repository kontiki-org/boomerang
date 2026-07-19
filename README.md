# boomerang

Alerting engine built on Kontiki: producers publish `NormalizedAlert`; subscription
+ alert-engine resolve recipients; email / telegram notifiers deliver.

## Quickstart

```bash
make stack-up
```

Core stack:

- RabbitMQ + kontiki-registry
- subscription, alert-engine
- email-notifier (MailHog on :8025) + telegram-notifier
- `POST /alerts` via alert-engine (see `stack/alert_engine.yaml` for the token)

Optional earthquake demo producer:

```bash
make stack-up-demo
```

Stop everything:

```bash
make stack-down
```

Declare subscriptions / endpoints in `stack/*.yaml` (YAML is the primary config path).
