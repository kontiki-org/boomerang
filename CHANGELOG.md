# Changelog

## [Unreleased]

- Notifiers (email, telegram): handlers reduced to delivery only; drop
  `alerting.notification.delivered` / `.failed` events (failures surface through
  Kontiki exception / alerting).
- Alert-engine: trust the bus contract (`NormalizedAlert`) and subscription RPC
  recipient rows (no defensive skip of incomplete fields).
- Subscription: area criteria only via `area.<type>` (remove unused `area_type` /
  `area_value` facts); docs aligned.

## [0.3.1] - 2026-07-23

- Telegram structured alerts: banner title prefers humanized `event_type`
  (falls back to last category segment when missing). Category icons stay
  from `app.telegram.category_icons`.

## [0.3.0] - 2026-07-23

- Docs: subscription YAML keys described as **audience** then **rule id**
  (not end-user / not sent to notifiers); examples use `ops` / `quakes`.
- Docs: adds `docs/configuration.md` and `docs/boomerang-config.example.yaml`
  (Boomerang `app.*` reference, Kontiki-style).
- Telegram notifier: generic structured alert rendering — category emojis come
  from optional `app.telegram.category_icons` (YAML); attribute labels are
  auto-humanized; attribute order follows the producer dict. Removes hardcoded
  domain display tables from the formatter.
- Telegram structured alerts: always show the alert **body** as a `Message:` line
  when it adds information beyond the title (including when attributes are
  present). Fixes dropped exception text and similar free-form bodies.

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
