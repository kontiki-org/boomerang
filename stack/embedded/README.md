# Embedded stack YAML
#
# Loaded by `make stack-embedded-up` (see docs/boomerang/DEPLOYMENT_EMBEDDED.md).
#
# Files:
# - subscription.yaml — Registry connector + declarative ops subscriptions
# - email_notifier.yaml — SMTP (MailHog locally) + `app.endpoints`
# - telegram_notifier.yaml — Telegram + `app.endpoints`
# - demo_app.yaml — demo Kontiki app (set_degraded via `make demo-app-degrade`)
#
# Shared with platform: `../common.services.yaml`, `../alert_engine.yaml`,
# `../kontiki_registry_alert.yaml`, `../kontiki_registry.yaml`, …
