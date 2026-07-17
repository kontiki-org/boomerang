# Quick mode — official formulation

This file helps an assistant **execute** Quick mode.
Authoritative rules live in `.engineering/` (especially `WORKFLOW.md`, `GHERKIN.md`, `SIMPLICITY.md`, `PUBLIC_SURFACE.md`).
Do not paste this whole file into chat unless the user asks to force Quick mode.

## Goal

A working connector as fast as possible — maximise progress and the “wow” effect.

## Do

1. Respect `AGENTS.md` and `.engineering/`.
2. After mode choice: **technical Starter Kit state check only** (not git archaeology).
3. Ask: *Describe the alert source or business need you want to implement.* **Wait** for the answer.
4. Short discovery on **the user's answer only** (≤ ~3 exchanges if needed).
5. Quality acknowledgment + assumptions summary; get **one global confirmation**, then implement.
6. In **one pass**: declarative features, production code, Behave steps.
7. Polling: immediate first poll, then every **60 seconds** (Starter convention).
8. Replace pedagogical `emit_demo_alert` with the real domain mechanism; update `demo/stack/` subscriptions/endpoints to match the catalog.
9. Stay inside the canonical tree (`src/connector/`, `tests/integration/`, …).
10. Run `make test`; auto-correct until green or a real human blocker.
11. Point the user to `make stack-up` → `make run-local` → **MailHog** (`:8025`). After updating `demo/stack/`: **`make stack-down`** at the end of generation; then **`stack-up`** + **`run-local`** when observing.
12. Auto-review checklist in `WORKFLOW.md`; document Assumptions in the README.
13. Announce Definition of Done only when satisfied.

## Do not

- Infer the connector domain from branch name, git history, stashes, deleted files, other branches, or prior connector code — unless the user explicitly asks for reuse or comparison.
- Use `git show`, branch trees, commit history, tags, or stashes to read or copy a prior connector's features, delegate, service, mocks, or steps during fresh generation.
- Read `boomerang/services/alert_services/*` or other monorepo producers as implementation reference unless the user explicitly asks.
- Rebuild project structure or invent parallel architecture.
- Import outside the public surface (stop and propose an API change instead).
- Ask questionnaires; prefer assumptions + one confirmation **after** the user has stated the need.
- Invent a long polling interval (e.g. one hour).
- Guide first demo via Telegram/SMS instead of MailHog email.
- Dump `.engineering/` into the user chat.
