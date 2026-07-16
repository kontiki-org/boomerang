# Gherkin conventions

See also: `PHILOSOPHY.md`, `WORKFLOW.md`.

Features are the behavioural source of truth. Step definitions execute the specification; they must not invent behaviour missing from the features.

## Rules

Features must be declarative, autonomous, and readable without opening step definitions.

A reader must understand:

- connector configuration;
- initial state;
- simulated source data (when relevant);
- the action performed;
- published alerts and other expected outcomes.

Scenarios should:

- use domain vocabulary;
- avoid vague wording;
- show important data in examples, tables, DocStrings, or configuration blocks;
- not hide business behaviour in fixtures or steps;
- avoid purely technical steps about the test framework.

## Prefer

- `Given the external API returns the following payload`
- `Then the connector publishes the following normalized alert`
- `Then no alert is published`

## Avoid

- `Given a valid response`
- `Then the result is correct`
- `Then the mocked messenger contains one event`

## Starter demo

The pedagogical demo uses `emit_demo_alert`. Real connectors replace that action with domain steps (poll, event received, webhook called, …) and update features accordingly.

## Location

- Features: `tests/integration/features/`
- Steps: `tests/integration/steps/`
- Tag: `@alert_connector_starter` (or a project-specific tag once the demo is replaced)
