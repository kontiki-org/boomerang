# Simplicity

See also: `PHILOSOPHY.md`.

## Fundamental rule

> The simplest implementation that completely satisfies the specification is the correct implementation.

The goal is **obvious code**, not generic code.

A developer opening the project should understand the connector quickly before extending it.

## Prefer

- flat, readable modules (`service`, `delegate`, `catalog`);
- direct Kontiki decorators (`@rpc`, `@task`, `@on_event`);
- slight duplication when it keeps the flow obvious.

## Avoid unless a real requirement appears

- interfaces, factories, builders, strategies;
- repository layers;
- extra “service” layers;
- elaborate configuration systems;
- abstractions “for later”.

Every abstraction needs at least one concrete requirement encountered during development.

## Relation to architecture

Keep the canonical shape (`WORKFLOW.md`). Simplicity applies inside that shape — do not invent a parallel architecture in the name of elegance.
