# Changelog

## [0.2.0] - 2026-07-21

- Requires Kontiki `>=1.3.0`. Compose healthchecks use the registry live probe
  `GET /live/{service}` (including bus-only notifiers), instead of process cmdline
  or service-local HTTP docs checks.
- Simplifies the earthquake demo: drops the fake `subscription_area` label;
  alerts use empty `areas`; catalog criterion is magnitude only. README demo
  subscription filters on `magnitude >= 4.5`.
- README: adds Install (`kontiki-boomerang` / `boomerang-contracts`).
- Subscription rules: `criteria` is optional; omit it for attribute catch-all
  (no more `key: "*"` / `value: "*"` no-op). When present, `all_of` must be
  non-empty. Legacy `*/*` criteria still match.

## [0.1.0] - 2026-07-19

Initial public release on PyPI (`kontiki-boomerang`, `boomerang-contracts`).

- YAML-only core: `subscription-service`, `alert-engine-service` (`alert.normalized`,
  `POST /alerts`), email and telegram notifiers (`app.endpoints`).
- Shared contracts package for producers and notifiers.
- Demo producer `earthquake-feed-service` and Compose quickstart (Telegram).
- See `docs/features.md` and `docs/contracts.md`.
