# Engineering mode — official formulation

This file helps an assistant **execute** Engineering mode.
Authoritative rules live in `.engineering/` (especially `WORKFLOW.md`, `GHERKIN.md`, `SIMPLICITY.md`, `PUBLIC_SURFACE.md`).
Do not paste this whole file into chat unless the user asks to force Engineering mode.

## Goal

A durable, reviewable connector (official or long-lived work) following the Boomerang engineering workflow.

## Do

1. Respect `AGENTS.md` and `.engineering/`.
2. After mode choice: **technical Starter Kit state check only** (not git archaeology).
3. Ask: *Describe the alert source or business need you want to implement.* **Wait** for the answer.
4. Short discovery on **the user's answer only** (≤ ~3 exchanges if needed).
5. Quality acknowledgment + assumptions summary; confirm before writing features.
6. Write **declarative `.feature` files only** (`GHERKIN.md`).
7. **Stop for human review** of the features. Do not implement code until the user approves.
8. After approval: production code + Behave steps; replace pedagogical `emit_demo_alert`; update `demo/stack/` to match the catalog.
9. Polling: immediate first poll, then every **60 seconds** (Starter convention).
10. Stay inside the canonical tree (`src/connector/`, `tests/integration/`, …).
11. Run `make test`; auto-correct until green or a real human blocker.
12. Point the user to `make stack-up` → `make run-local` → **MailHog** (`:8025`). After updating `demo/stack/`: **`make stack-down`** at the end of generation; then **`stack-up`** + **`run-local`** when observing.
13. Auto-review checklist in `WORKFLOW.md`; document Assumptions in the README.
14. Announce Definition of Done only when satisfied.

## Do not

- Infer the connector domain from branch name, git history, stashes, deleted files, other branches, or prior connector code — unless the user explicitly asks for reuse or comparison.
- Use `git show`, branch trees, commit history, tags, or stashes to read or copy a prior connector's features, delegate, service, mocks, or steps during fresh generation.
- Read `boomerang/services/alert_services/*` or other monorepo producers as implementation reference unless the user explicitly asks.
- Skip the feature-review stop.
- Rebuild project structure or invent parallel architecture.
- Import outside the public surface (stop and propose an API change instead).
- Hide business behaviour in step definitions.
- Invent a long polling interval (e.g. one hour).
- Guide first demo via Telegram/SMS instead of MailHog email.
- Dump `.engineering/` into the user chat.
