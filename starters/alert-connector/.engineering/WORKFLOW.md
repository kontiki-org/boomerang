# Workflow

See also: `PHILOSOPHY.md`.

## First interaction

The user typically arrives via `make start`, which displays the official entry prompt
(`.engineering/ENTRY_PROMPT.txt`) to paste into any AI assistant.

Before discussing the business problem, deliver the stable opening from `FIRST_MESSAGE.md`.

Then ask the user to choose a mode. The chosen mode remains the default for this project until they change it explicitly.

After mode choice, follow **Business intent vs repository context** and **Technical state check** below — **before** any domain discovery or implementation work.

## Business intent vs repository context

**The business requirement always comes from the user.**

The Starter Kit may infer **implementation details** from a stated business need (API choice, polling interval, dedupe, catalog fields). It must **never** infer the business need itself from repository context.

### Forbidden as product requirements (unless the user explicitly asks)

Do **not** use these to guess or pre-fill what the connector should do:

- current branch name
- commit messages
- git history
- deleted files
- other branches
- stashes
- previous connector implementations in this repo (including skeleton, rain demo, or prior dry-runs)

Do **not** search git history, inspect other branches, or read prior connector code **before** the user has described the alert source or business need — unless they explicitly ask for reuse, comparison, or continuity with a previous implementation.

Repository metadata may be used **only** for technical safety checks (see below), never as substitute for the user's business description.

### Required sequence after mode choice

1. **Technical state check** (Starter Kit readiness only).
2. Ask the user explicitly:

   > Describe the alert source or business need you want to implement.

3. **Wait** for the user's answer. Do not propose a domain, API, or connector theme until they have responded.
4. **Only then:** clarify if needed, discover candidate public APIs, build assumptions, prepare the plan, and generate.

Each dry-run must stand on its own. Inspecting a previous connector before the business need is known invalidates the Starter Kit as an independent validation of the method.

## Technical state check (after mode choice)

Before asking for the business need, you may verify **Starter Kit technical readiness** only, for example:

- required files and canonical tree present (`src/connector/`, `tests/integration/`, `.engineering/`, Makefile, …)
- dependencies installable (`make install` path plausible)
- working tree state if relevant to safe generation (e.g. warn if unexpected dirty state in starter files — do **not** interpret branch names or commit messages as requirements)

Keep this check brief. Do not turn it into repository archaeology.

## Modes

Mode behaviour is defined in this file. Short **execution checklists** also live in:

- `../.prompts/quick-mode.md`
- `../.prompts/engineering-mode.md`

Those prompts are formulations of the method, not a second source of truth.

### Quick mode

Goal: a working connector as fast as possible.

1. Technical state check (above).
2. Ask for the business need; **wait** for the user's answer.
3. Short discovery on **that answer only** (below).
4. Quality acknowledgment (below).
5. Assumptions summary + **one global confirmation** (below) — then implement.
6. Implement features, production code, and steps in one pass.
7. Run `make test`; auto-correct until green (or a real blocker).
8. Help the user run locally and see an **email** notification via MailHog (below).
9. Auto-review (below); document Assumptions in the README.
10. Announce Definition of Done only when satisfied.

Maximise progress and the “wow” effect. Ask as few questions as possible — but **never** skip waiting for the business description.

### Engineering mode

Goal: durable, reviewable work (official or long-lived connectors).

1. Technical state check (above).
2. Ask for the business need; **wait** for the user's answer.
3. Short discovery on **that answer only** (below).
4. Quality acknowledgment (below).
5. Assumptions summary + confirmation (below).
6. Write declarative `.feature` files only.
7. **Stop for human review** of the features.
8. After approval: implement production code and step definitions.
9. Run `make test`; auto-correct until green (or a real blocker).
10. Help with the MailHog email demo path when relevant (below).
11. Auto-review; document Assumptions in the README.
12. Announce Definition of Done only when satisfied.

## Discovery

Discovery starts **only after** the user has described the alert source or business need.

Understand the business problem from **their words**, not from repository metadata.

Never ask a question whose answer can reasonably be inferred **from what the user already said**.
Usually at most three short exchanges after the initial description. If ambiguity remains, ask **one** focused question — never a questionnaire.

Typical subjects (once the user has spoken):

- What should be monitored?
- Where do the data come from?
- When should an alert be emitted?

Do not propose a connector domain, search git, or open prior implementations until this step.

## Quality acknowledgment (before generation)

Before generating, briefly remind the user that result quality depends on the clarity of the need they expressed, and that inferred assumptions will shape the connector.

Ask for a short confirmation, for example:

> I understand that the result will depend on the assumptions taken from my description.

Do not discourage the user. Do not turn this into a long disclaimer.

## Assumptions before implementation

Structural choices must be visible **before** coding — not only at the end.

After discovery (and the quality acknowledgment), show a clear summary of retained assumptions, for example:

- data source;
- polling or event trigger;
- dedupe strategy;
- geographic or entity coverage;
- severity mapping;
- external identifier.

**Quick mode:** one global confirmation of that summary is enough, then implement.
**Engineering mode:** same summary; then proceed to features (with the usual review stop).

Do not turn this into a questionnaire. Infer implementation choices aggressively **from the user's stated need**; surface them in the assumptions table.

Also keep an **Assumptions** section in the README (and optionally repeat a short summary at the end of generation).

## Polling convention

For **all** polling-based connectors generated with this kit:

1. First poll **immediately** at startup (`immediate=True` or equivalent).
2. Then poll every **60 seconds**.

This interval is intentional and short so the user can verify the connector quickly.
It is **not** a production recommendation. Do not invent a different default (e.g. one hour).

Document in Assumptions that 60s is a Starter Kit demo convention.

## Local demonstration (V1)

The official first-experience notification channel is **email only**, observed via **MailHog**.

Guide the user from **this starter directory**:

```text
make stack-up → make run-local → observe MailHog (http://localhost:8025)
```

- `make stack-up` starts the autonomous demo stack (RabbitMQ, MailHog, kontiki-registry plumbing, subscription, alert-engine, email-notifier). Config lives under `demo/stack/`.
- `make run-local` runs **only the connector** on the host.
- Skeleton proof: `make emit-demo` calls pedagogical `emit_demo_alert` (replaced for real connectors).
- After generating a real connector: update `demo/stack/` subscriptions/endpoints to match the catalog; the user observes via the real domain mechanism (not `emit-demo`).

### After updating `demo/stack/` (end of generation)

YAML under `demo/stack/` is loaded **only at process start**. Editing it while the stack is up does **not** apply.

At the **end** of generation (after writing/updating `demo/stack/`):

1. Tell the user to run **`make stack-down`** so no stale subscription/endpoint config keeps running.
2. For the MailHog demo, the path is then fresh: **`make stack-up`** → **`make run-local`** (and restart `run-local` if it was already running — connector in-memory dedupe is otherwise stale).

Do not claim MailHog will show notifications from the new catalog until the stack has been brought down and up again with the new YAML.

(`make stack-restart` is an optional shortcut for down+up; the default instruction after generation is **`stack-down`**, then **`stack-up`** when the user is ready to observe.)

Telegram, SMS, and other notifiers are **out of scope** for the official first demo path.

`make test` is for the AI/maintainer correction loop — not a required end-user step before MailHog.

## Canonical structure

This repository defines the **canonical** connector layout:

- `src/connector/` — `service.py`, `delegate.py`, `catalog.py`, `main.py`
- `tests/integration/` — Behave features, steps, local event catcher
- `config/local.yaml`
- `demo/stack/` — autonomous demo Compose config (AI updates on generation)
- `docker-compose.yaml` — `make stack-up`
- `.engineering/` — method (maintainers / assistants)
- `.prompts/` — mode execution checklists
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

- [ ] Business need came from the user — not from branch/git/history/prior connector code
- [ ] Obvious code; no unnecessary abstractions (`SIMPLICITY.md`)
- [ ] Only public-surface imports (`PUBLIC_SURFACE.md`)
- [ ] Features declarative and autonomous (`GHERKIN.md`)
- [ ] Polling connectors use immediate + 60s convention (if applicable)
- [ ] `make test` green
- [ ] Assumptions were shown before implementation and documented in README
- [ ] Demo path explained via email / MailHog when guiding local observation
- [ ] If `demo/stack/` changed: user told to `make stack-down`, then `stack-up` + `run-local` for demo
- [ ] Ready for human review

## Automatic correction loop

If `make test` fails or the Definition of Done is not met: **do not stop**.
Iterate (fix → retest → re-review) until DoD is met **or** a **real blocker** needs a human (non-inferable business ambiguity, missing public API — see `PUBLIC_SURFACE.md`, infrastructure down, etc.).

## README

Keep the README a short product path: `make start`, install, `stack-up` / `run-local` / MailHog, Assumptions section.
Mention `stack-down` after generation when `demo/stack/` changed. Mention `make test` only as the AI/maintainer loop. Do not dump the engineering method into the README.
