# UI Proposal for Boomerang

> **Positioning note (updated)**  
> This document is intentionally kept as the **long-term web UI reminder** (Vue/Nuxt direction).
>  
> The **short-term implementation track** is a **Textual UI** communicating over **AMQP/RPC**.
>  
> The architectural principles described here still apply to both tracks:
> modularity, extensibility, capability-driven composition, and decoupling from specific providers.

## Context and goals

Boomerang is designed to be extensible on both sides of the alert pipeline:

- upstream: multiple alert producer services,
- downstream: multiple alert delivery/processing services,
- deployment: self-hostable in heterogeneous environments.

The UI must follow the same principles:

- modular and extensible by design,
- usable in a minimal setup and scalable for advanced setups,
- decoupled from specific providers/channels,
- operable by administrators and end users.

## Product principles for the UI

1. Plugin-first, not hardcoded-first
   - The UI should discover available capabilities (sources, channels, processors) from backend metadata.
   - New service types should appear in UI with minimal or no core changes.

2. Configuration over customization
   - Most behavior should come from declarative manifests and server-side config.
   - Avoid forking the UI codebase for each deployment.

3. Readable and maintainable architecture
   - Strict separation between:
     - domain models,
     - application/use-case logic,
     - provider adapters (HTTP clients),
     - presentation components.

4. Progressive complexity
   - Small installations get a simple dashboard.
   - Large installations can enable advanced modules (observability, workflow tuning, plugin settings).

5. Self-hosting by default
   - No mandatory SaaS dependency.
   - Works behind reverse proxies, private networks, and custom auth setups.

## Suggested stack (long-term web target)

- Framework: Vue 3 + Nuxt 3 + TypeScript
- State management: Pinia
- Data layer: composables + typed API clients (optionally TanStack Query for Vue if needed)
- Validation: Zod
- UI components: a consistent component library (for example Nuxt UI or Vuetify)
- Tooling: ESLint + Prettier + Vitest + Playwright

Why this stack for Boomerang:

- approachable for backend-first contributors,
- strong conventions via Nuxt,
- modular architecture with explicit boundaries,
- good fit for self-hosted operations portals.

## UI architecture proposal

### 1) Core shell app

Core app provides:

- routing,
- authentication/session handling,
- global layout and navigation,
- plugin/module registry,
- permissions and feature flag checks,
- standardized error/loading states.

The shell must stay stable and small.

### 2) Domain modules

Each business capability lives in its own module:

- `identity` (auth/session),
- `subscriptions`,
- `endpoints`,
- `alerts` (normalized alert visibility),
- `deliveries` (delivery outcomes),
- `plugins` (installed providers/services).

A module includes:

- types/contracts,
- API adapter(s),
- use-cases,
- pages/components.

### 3) Extension modules (plugin UI)

Extension modules represent service-specific UIs, such as:

- earthquake source settings,
- email provider diagnostics,
- SMS provider controls,
- future connectors (webhook, push, chatops, etc.).

Each extension module should be mounted through a manifest contract, for example:

- module id and version,
- navigation entries,
- required capabilities,
- settings schema,
- optional widgets for dashboards.

## Capability-driven UI model

To support extensibility, backend should expose a capabilities endpoint (or equivalent metadata contract), for example:

- available channels (`email`, `sms`, ...),
- available alert categories/event types,
- installed source services,
- installed notifier/processor services,
- optional feature flags.

The UI renders from capabilities:

- forms adapt to allowed channels/events,
- pages appear/hide based on installed services,
- plugin settings pages are generated from service metadata where possible.

## Multi-tenant and role model (forward-compatible)

Even if initial deployment is single-tenant, design for future extension:

- roles: `admin`, `operator`, `user`, `readonly`,
- scope: global vs organization/project/environment,
- policy-aware navigation (menu items filtered by permissions).

## Self-hosting requirements

1. Deployment compatibility
   - support reverse proxy base path,
   - configurable API base URL,
   - container-friendly runtime config.

2. Security baseline
   - strict CSP support (where feasible),
   - secure token handling,
   - audit-friendly action logging hooks.

3. Offline/air-gapped friendliness
   - avoid hard dependency on third-party CDNs,
   - bundle assets locally.

4. Ops friendliness
   - health page for UI/API connectivity checks,
   - explicit version display (UI version + backend service versions).

## UX proposal (functional areas)

1. Overview
   - pipeline health summary,
   - recent alert flow,
   - delivery success/failure trends.

2. My subscriptions
   - create/update/pause/delete subscriptions,
   - channel preferences and quiet hours,
   - endpoint mapping visibility.

3. Endpoints
   - manage email/SMS endpoints,
   - default endpoint designation per channel,
   - per-endpoint status.

4. Sources and processors
   - list installed source services and downstream processors,
   - per-service config/status pages provided by extension modules.

5. Observability
   - recent events timeline,
   - delivery outcome explorer,
   - filtering by alert id, recipient id, channel, service.

## Suggested repository placement

Keep the UI in the same repository (monorepo style), for example:

- `apps/web` for Nuxt app,
- `boomerang/services/*` for backend services,
- shared contracts in a dedicated location if needed.

This keeps API/UI evolution synchronized while preserving clear boundaries.

## Developer experience and orchestration (Make-first)

To keep iterations fast and reliable, Boomerang should use `make` as the single local orchestration entrypoint for backend + frontend workflows.

Why:

- standard and familiar for self-hosted/backend-centric teams,
- reproducible commands across local and CI environments,
- lower cognitive load for regular end-to-end POC iterations.

Minimum target set to introduce early:

- `make platform-up`
  - starts required local dependencies (for example AMQP, Mailhog) and platform services,
  - starts frontend dev server when UI exists.
- `make platform-down`
  - stops the full local stack cleanly.
- `make web-dev`
  - starts only the frontend in dev mode.
- `make web-build`
  - builds frontend production artifacts.
- `make web-preview`
  - serves production build locally for verification.
- `make web-deploy-local`
  - deploys frontend artifact to a local/self-hosted target used for end-to-end validation.
- `make e2e-smoke`
  - runs one short end-to-end verification scenario through the earthquake flow.
- `make help`
  - lists available commands and short descriptions.

Design guidelines for Make targets:

- keep targets idempotent where possible,
- keep names explicit and stable,
- use Make for orchestration, not complex business logic,
- move longer logic to scripts and call them from Make targets.

## MVP phased roadmap

Phase 1: Core self-service UI

- login via auth code,
- endpoint management (email/SMS),
- subscription CRUD,
- basic dashboard.

Phase 2: Extensibility foundation

- capabilities endpoint consumption,
- plugin/module registry,
- dynamic navigation from capabilities.

Phase 3: Operations and ecosystem

- delivery explorer,
- source/processor management views,
- plugin configuration UI contracts.

## Iterative learning plan (POC by POC)

Goal: learn the frontend stack progressively with regular end-to-end POCs that always include the earthquake source flow.

Rules for each iteration:

- keep scope intentionally small (one concept at a time),
- keep the POC functional end-to-end,
- include a short "what I learned" note,
- freeze architecture decisions only after at least two successful iterations.

Iteration 0: Bootstrap and run

- initialize `apps/web` with Nuxt + TypeScript,
- create one page that confirms frontend is running and can call one backend health endpoint,
- introduce baseline targets: `make platform-up`, `make platform-down`, `make web-dev`, `make help`,
- document run commands and local dev workflow.

Expected learning:

- project structure basics,
- routing and page conventions in Nuxt,
- first API call from frontend.

Iteration 1: Earthquake feed visibility

- create a simple "Earthquake alerts" page,
- display recent normalized alerts from a minimal backend endpoint or mock read model,
- show loading/error/empty/success states cleanly,
- add `make e2e-smoke` first version for this flow.

Expected learning:

- data fetching lifecycle,
- typed data contracts,
- reusable UI state patterns.

Iteration 2: Authentication flow (identity)

- implement request auth code + consume auth code screens,
- store session token safely for subsequent API calls,
- add route guard for one protected page,
- add `make web-build` and `make web-preview` for reproducible local release checks.

Expected learning:

- form handling and validation,
- authentication state handling,
- protected routes.

Iteration 3: Endpoints management (email/SMS)

- CRUD page for email and SMS endpoints,
- explicit success/error UX feedback,
- keep API adapters isolated from UI components.

Expected learning:

- modular architecture boundaries,
- practical CRUD patterns,
- error-handling consistency.

Iteration 4: Subscription CRUD with earthquake context

- create/list/update/pause/delete subscriptions,
- prefill category/event suggestions from allowed alerts/channels,
- include earthquake-related categories in examples and default walkthrough.

Expected learning:

- complex forms and normalization,
- richer state transitions,
- reusable composables/store actions.

Iteration 5: End-to-end pipeline view

- add a basic "Alert journey" page:
  - normalized alert seen,
  - notification requested,
  - delivery outcome (delivered/failed),
- filter by alert id and channel.
- stabilize `make e2e-smoke` to cover auth + subscription + earthquake alert journey.

Expected learning:

- cross-service UI composition,
- observability basics for operators,
- preparing plugin-ready UI boundaries.

Iteration 6: First extensibility slice

- introduce a basic plugin registry contract in UI,
- register one source plugin card (earthquake) and one notifier plugin card (email or SMS),
- make navigation entries capability-driven,
- add `make web-deploy-local` for self-hosted end-to-end testing.

Expected learning:

- extension contract design,
- dynamic navigation/rendering,
- safe evolution path for future services.

Definition of done for each iteration:

- local setup documented in `README`,
- at least one happy path demonstrated,
- at least one failure path demonstrated,
- small retro note added in docs: what was clear, what was confusing, what to simplify next.

## Open design questions

1. Should plugin UI modules be loaded:
   - at build time only, or
   - with runtime-discoverable remote modules?

2. Where should capabilities metadata live:
   - centralized gateway endpoint, or
   - aggregated from services client-side?

3. Should the first release include:
   - only user self-service UX, or
   - admin/ops UX from day one?

4. What is the target role model for v1:
   - simple authenticated user/admin split, or
   - more granular RBAC?

## Decision proposal

Use a two-horizon approach:

- short term: deliver a modular Textual UI on top of AMQP/RPC contracts;
- longer term: deliver a modular monorepo web UI (`apps/web`) based on Nuxt/Vue and a capability-driven rendering model.

In both horizons, prioritize self-service workflows first, while defining extension contracts early so new source/notifier/processor services can integrate with minimal core UI changes.
