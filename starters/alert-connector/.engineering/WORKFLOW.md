# Workflow

See also: `PHILOSOPHY.md`.

## First interaction

The user typically arrives via `make start`, which displays the official entry prompt
(`.engineering/ENTRY_PROMPT.txt`) to paste into any AI assistant.

Before discussing the business problem, deliver the stable opening from `FIRST_MESSAGE.md`.

Then ask the user to choose a mode. The chosen mode remains the default for this project until they change it explicitly.

## Modes

Mode behaviour is defined in this file. Short **execution checklists** also live in:

- `../.prompts/quick-mode.md`
- `../.prompts/engineering-mode.md`

Those prompts are formulations of the method, not a second source of truth.

### Quick mode

Goal: a working connector as fast as possible.

1. Short discovery (below).
2. Implement features, production code, and steps in one pass.
3. Run `make test`; auto-correct until green (or a real blocker).
4. Help the user run locally and see an alert when the stack is available.
5. Auto-review (below); document Assumptions in the README.
6. Announce Definition of Done only when satisfied.

Maximise progress and the “wow” effect. Ask as few questions as possible.

### Engineering mode

Goal: durable, reviewable work (official or long-lived connectors).

1. Short discovery (below).
2. Write declarative `.feature` files only.
3. **Stop for human review** of the features.
4. After approval: implement production code and step definitions.
5. Run `make test`; auto-correct until green (or a real blocker).
6. Auto-review; document Assumptions in the README.
7. Announce Definition of Done only when satisfied.

## Discovery

Understand the business problem, not every technical detail.

Never ask a question whose answer can reasonably be inferred.
Usually at most three short exchanges. If ambiguity remains, ask **one** focused question — never a questionnaire.

Typical subjects:

- What should be monitored?
- Where do the data come from?
- When should an alert be emitted?

## Assumption-driven development

If information is missing but a reasonable assumption exists: assume it, document it, continue.
Interrupt the user only when the ambiguity would change functional behaviour.

Record important assumptions in the README **Assumptions** section (and optionally summarise at the end of the generation). Examples: polling interval, dedupe strategy, severity mapping, external id.

## Canonical structure

This repository defines the **canonical** connector layout:

- `src/connector/` — `service.py`, `delegate.py`, `catalog.py`, `main.py`
- `tests/integration/` — Behave features, steps, local event catcher
- `config/local.yaml`
- `.engineering/` — method (maintainers / assistants)
- root `README.md`, `AGENTS.md`, `Makefile`

Do **not** reinvent this structure. Domain creativity belongs in mapping and criteria, not in project shape.

Replace the pedagogical `emit_demo_alert` RPC with the real domain mechanism (`@task`, `@on_event`, webhook, …). That RPC is Starter-only pedagogy, not recommended architecture.

## Definition of Done

A connector is done when it:

- starts successfully;
- passes the full test suite (`make test`);
- publishes valid `NormalizedAlert` events;
- exposes a correct subscription catalog;
- follows Starter Kit conventions (structure, public surface, Gherkin, simplicity).

Not required: production-perfect hardening. Required: a clean first implementation ready for human review.

## Auto-review (mandatory before claiming done)

- [ ] Obvious code; no unnecessary abstractions (`SIMPLICITY.md`)
- [ ] Only public-surface imports (`PUBLIC_SURFACE.md`)
- [ ] Features declarative and autonomous (`GHERKIN.md`)
- [ ] `make test` green
- [ ] Assumptions documented in README
- [ ] Ready for human review

## Automatic correction loop

If `make test` fails or the Definition of Done is not met: **do not stop**.
Iterate (fix → retest → re-review) until DoD is met **or** a **real blocker** needs a human (non-inferable business ambiguity, missing public API — see `PUBLIC_SURFACE.md`, infrastructure down, etc.).

## README

Keep the README a short product path: install, test, run, stack assumptions, Assumptions section.
Do not dump the engineering method into the README.
