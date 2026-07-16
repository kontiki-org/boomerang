# Quick mode — official formulation

This file helps an assistant **execute** Quick mode.
Authoritative rules live in `.engineering/` (especially `WORKFLOW.md`, `GHERKIN.md`, `SIMPLICITY.md`, `PUBLIC_SURFACE.md`).
Do not paste this whole file into chat unless the user asks to force Quick mode.

## Goal

A working connector as fast as possible — maximise progress and the “wow” effect.

## Do

1. Respect `AGENTS.md` and `.engineering/`.
2. After mode choice: short discovery (infer aggressively; ≤ ~3 exchanges).
3. In **one pass**: declarative features, production code, Behave steps.
4. Replace pedagogical `emit_demo_alert` with the real domain mechanism.
5. Stay inside the canonical tree (`src/connector/`, `tests/integration/`, …).
6. Run `make test`; auto-correct until green or a real human blocker.
7. Auto-review checklist in `WORKFLOW.md`; document Assumptions in the README.
8. Announce Definition of Done only when satisfied.

## Do not

- Rebuild project structure or invent parallel architecture.
- Import outside the public surface (stop and propose an API change instead).
- Ask questionnaires; prefer assumptions + README documentation.
- Dump `.engineering/` into the user chat.
