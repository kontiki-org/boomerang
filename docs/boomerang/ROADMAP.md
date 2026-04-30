# Boomerang — Enhancements & roadmap

This document captures **planned enhancements** and **open decisions**.

If you want the current implemented architecture, see **`docs/boomerang/EXISTING.md`**.

---

## Product direction (summary)

- **Dual mission**
  - **Kontiki showcase**: credible patterns for tasks, messaging, RPC, and integration tests.
  - **Usable hostable product**: something you can run on a home server/VPS and rely on.

- **Hostable by default**: clear deployment story, minimal external dependencies.
- **Extension without forking**: add new sources/channels as separate services.
- **Contracts over conventions**: evolve `alert.normalized` and notification contracts deliberately.
- **Human access**: keep HTTP APIs stable; prioritize a Textual client on AMQP/RPC in the near term, with web UI as a later horizon.

---

## Near-term objective (first audience)

- **End-to-end demo with `earthquake-feed-service`**
  - reproducible path from clone to live notification (SMS or email)
  - minimal commands + documented configuration
- **A sober Textual UI for subscribing and operating**
  - sign-in / auth flow
  - managing delivery endpoints (email, SMS)
  - creating subscriptions and attaching channels via endpoint keys

---

## Roadmap (phased)

### Phase 1 — Core self-service UX

- sign-in / auth code UX on top of `identity-service` (Textual, AMQP/RPC-first)
- endpoint management (email/SMS)
- subscription CRUD
- basic dashboard (pipeline + recent alerts)

### Phase 2 — Extensibility foundation

- define and ship a **capabilities catalog** (backend metadata contract)
- UI renders navigation and forms from capabilities
- plugin/module registry (UI-side) driven by capabilities

### Phase 3 — Operations and ecosystem

- delivery explorer + recent events timeline
- source/processor management views
- plugin configuration UI contracts

---

## UI proposal (tracked direction)

Key decisions to make early:

- **plugin UI loading model**: build-time modules first; revisit runtime remote modules later
- **capabilities endpoint**: prefer a central/gateway endpoint initially (avoid client aggregation)
- **v1 audience**: prioritize user self-service workflows; add admin/ops views incrementally
- **RBAC**: start simple (`admin` / `user`), keep room for extension

---

## Open design questions (current)

1. **Capabilities “source of truth”**: gateway vs aggregated from services?
2. **Plugin UI strategy**: build-time only vs runtime remote modules?
3. **Role model**: simple split vs granular RBAC, and when to introduce multi-tenant scoping?
4. **Observability data model**: which read model do we standardize on for timeline/explorer?

---

## Strategic directions (intentions)

- **Authoring experience**: shared helpers/patterns/SDK so new sources and channels are quick to implement and test.
- **Operator + user experience**: packaged compose (or equivalent), sensible defaults, lightweight visibility into delivery health.
- **UI extensibility**: clients driven by HTTP APIs + a capability catalog (avoid hard-coded forks).

---

## Success criteria

- A motivated user can **self-host**, subscribe, attach endpoints, and receive **real notifications** from **real connectors**.
- A developer can add a **new normalized source** or a **new channel** by implementing the edge, reusing the core and test patterns.
- The repository remains a **credible Kontiki reference** without sacrificing clarity of the alerting domain model.

---

## Cleanup / documentation policy

To keep docs maintainable as implementation advances:

- **Only two living docs**:
  - `docs/boomerang/EXISTING.md` (what exists)
  - `docs/boomerang/ROADMAP.md` (what’s next)
- Other documents in `docs/boomerang/` are treated as **historical/archived** and should contain a short notice at the top pointing to the two documents above.
