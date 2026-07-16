# Quick mode — official formulation

This file helps an assistant **execute** Quick mode.
Authoritative rules live in `.engineering/` (especially `WORKFLOW.md`, `GHERKIN.md`, `SIMPLICITY.md`, `PUBLIC_SURFACE.md`).
Do not paste this whole file into chat unless the user asks to force Quick mode.

## Goal

A working connector as fast as possible — maximise progress and the “wow” effect.

## Do

1. Respect `AGENTS.md` and `.engineering/`.
2. After mode choice: short discovery (infer aggressively; ≤ ~3 exchanges).
3. Quality acknowledgment + assumptions summary; get **one global confirmation**, then implement.
4. In **one pass**: declarative features, production code, Behave steps.
5. Polling: immediate first poll, then every **60 seconds** (Starter convention).
6. Replace pedagogical `emit_demo_alert` with the real domain mechanism; update `demo/stack/` subscriptions/endpoints to match the catalog.
7. Stay inside the canonical tree (`src/connector/`, `tests/integration/`, …).
8. Run `make test`; auto-correct until green or a real human blocker.
9. Point the user to `make stack-up` → `make run-local` → **MailHog** (`:8025`) for the official local demo.
10. Auto-review checklist in `WORKFLOW.md`; document Assumptions in the README.
11. Announce Definition of Done only when satisfied.

## Do not

- Rebuild project structure or invent parallel architecture.
- Import outside the public surface (stop and propose an API change instead).
- Ask questionnaires; prefer assumptions + one confirmation.
- Invent a long polling interval (e.g. one hour).
- Guide first demo via Telegram/SMS instead of MailHog email.
- Dump `.engineering/` into the user chat.
