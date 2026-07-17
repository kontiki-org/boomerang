# Agents

Follow the official Boomerang connector engineering method under `.engineering/`.

Those rules take precedence over assistant defaults, generic coding advice, and any conflicting local habit.

## Read in this order

1. `.engineering/PHILOSOPHY.md` — founding principles
2. `.engineering/FIRST_MESSAGE.md` — stable opening (product UX)
3. `.engineering/WORKFLOW.md` — modes, discovery, DoD, correction loop
4. `.engineering/PUBLIC_SURFACE.md` — allowed imports
5. `.engineering/GHERKIN.md` — declarative features
6. `.engineering/SIMPLICITY.md` — obvious code

Optional mode formulations (execution aids, not the method itself):

- `.prompts/quick-mode.md`
- `.prompts/engineering-mode.md`

## Immediate behaviour

When the user sends the official entry prompt (`Start the Boomerang Starter Kit.` — see `.engineering/ENTRY_PROMPT.txt` / `make start`):

1. Deliver the first message (`FIRST_MESSAGE.md`) if the session has not already chosen a mode.
2. After mode choice: **technical Starter Kit state check only**, then ask for the business need and **wait** for the answer. Never infer the domain from git branch, history, stashes, deleted files, other branches, or prior connector implementations unless the user explicitly asks.
3. Run discovery and generation per `WORKFLOW.md` (quality acknowledgment, assumptions confirmation, then implement; use `.prompts/*` only as a short mode checklist).
4. Stay inside the canonical tree (`src/connector/`, `tests/integration/`, …).
5. Replace pedagogical `emit_demo_alert` when implementing a real domain connector.
6. Polling connectors: immediate + 60s. Guide local observation via **email / MailHog** (`make stack-up` → `make run-local`). After updating `demo/stack/`: tell the user **`make stack-down`** (end of generation), then **`stack-up`** + **`run-local`** to observe.
7. Auto-review and iterate until Definition of Done or a real human blocker.

The entry prompt stays deliberately short. Do not expect the user to paste `.engineering/` or `.prompts/` into the chat.
