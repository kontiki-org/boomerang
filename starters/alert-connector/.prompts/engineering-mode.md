# Engineering mode — official formulation

This file helps an assistant **execute** Engineering mode.
Authoritative rules live in `.engineering/` (especially `WORKFLOW.md`, `GHERKIN.md`, `SIMPLICITY.md`, `PUBLIC_SURFACE.md`).
Do not paste this whole file into chat unless the user asks to force Engineering mode.

## Goal

A durable, reviewable connector (official or long-lived work) following the Boomerang engineering workflow.

## Do

1. Respect `AGENTS.md` and `.engineering/`.
2. After mode choice: short discovery (infer aggressively; ≤ ~3 exchanges).
3. Quality acknowledgment + assumptions summary; confirm before writing features.
4. Write **declarative `.feature` files only** (`GHERKIN.md`).
5. **Stop for human review** of the features. Do not implement code until the user approves.
6. After approval: production code + Behave steps; replace pedagogical `emit_demo_alert`; update `demo/stack/` to match the catalog.
7. Polling: immediate first poll, then every **60 seconds** (Starter convention).
8. Stay inside the canonical tree (`src/connector/`, `tests/integration/`, …).
9. Run `make test`; auto-correct until green or a real human blocker.
10. Point the user to `make stack-up` → `make run-local` → **MailHog** (`:8025`). After updating `demo/stack/`: **`make stack-down`** at the end of generation; then **`stack-up`** + **`run-local`** when observing.
11. Auto-review checklist in `WORKFLOW.md`; document Assumptions in the README.
12. Announce Definition of Done only when satisfied.

## Do not

- Skip the feature-review stop.
- Rebuild project structure or invent parallel architecture.
- Import outside the public surface (stop and propose an API change instead).
- Hide business behaviour in step definitions.
- Invent a long polling interval (e.g. one hour).
- Guide first demo via Telegram/SMS instead of MailHog email.
- Dump `.engineering/` into the user chat.
