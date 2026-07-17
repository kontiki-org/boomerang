# Philosophy

This file states the founding principles of the Boomerang Alert Connector Starter Kit.
Other documents in `.engineering/` refine how to apply them; they should not restate these principles at length.

## What this kit is

The Starter Kit is the **reference implementation** of the official method for building Boomerang alert producers.

It is an engineering method first. Assistants, if used, are executors of that method — not the product.

It eliminates the blank page: clone, describe the domain, obtain a working connector that follows Boomerang conventions.

## What the generated connector is

The generated connector is a **first iteration**:

- simple, readable, easy to review, easy to extend;
- **not** the final architecture of the project.

The developer is expected to evolve it afterwards with confidence.

## What a connector does

A Boomerang connector transforms observable information into deterministic alerts.

If no observable data source or deterministic decision rule exists, the Starter Kit should explain the limitation and, whenever possible, help the user reformulate the problem into one that can be implemented.

## How work should feel

- The **business need always comes from the user** — never from branch names, git history, or prior connector code in the repo (unless the user explicitly asks to reuse or compare).
- **Fresh Starter generation** must not use other branches, commits, tags, stashes, or deleted implementations as hidden templates — only the current skeleton, public contracts, Starter rules, generic harness, and the stated requirement.
- Prefer **inference of implementation details** over questionnaires once the need is stated; document important assumptions **before** implementation as well as in the README.
- Prefer **obvious code** over generic frameworks (see `SIMPLICITY.md`).
- Keep the **canonical structure** of this repository; do not reinvent layout or style (see `WORKFLOW.md`).
- Treat the root `README.md` as **product UX** (fast path to a working connector), not as technical documentation.
- Users start the AI experience via **`make start`** (official entry prompt), not by pasting the method into chat.
- Polling connectors use the Starter Kit convention: immediate first poll, then every **60 seconds** (demo speed, not production).
- The official local demo notification path is **email via MailHog** only (V1).

## Authority

Rules in `.engineering/` prevail over an assistant’s default behaviour, generic best practices, and any conflicting local habit.

In case of conflict, the Starter Kit wins.

## Continuous improvement

Official connectors built with this kit should improve the kit itself.
After significant kit changes, at least one earlier connector should still be achievable with the same method without architectural regression.
