# Why the AI Starter Kit?

## Motivation

At first glance, the AI Starter Kit may look like "just a code generator".

It is not.

Its primary goal is to encode the official Boomerang connector development
method and dramatically reduce the time required to obtain a first working
connector.

The AI is only one component of this experience.

---

# From business idea to first alert

Traditional onboarding usually looks like this:

- read the documentation;
- understand Kontiki;
- understand Boomerang contracts;
- create a project;
- implement the service;
- write tests;
- prepare a demo configuration;
- launch everything;
- eventually receive the first alert.

The Starter Kit compresses this workflow into:

Business need

↓

Implementation assumptions

↓

Generation

↓

make test

↓

make run-local

↓

First alert received

The objective is not to eliminate human review.

The objective is to reach a runnable, reviewable implementation in minutes.

---

# More than code generation

The Starter does not only generate source files.

It encapsulates months of architectural decisions:

- project structure;
- service/delegate separation;
- public contracts;
- subscription catalogs;
- Behave integration tests;
- demo stack;
- configuration conventions;
- recommended implementation patterns.

Without the Starter, this knowledge would remain scattered across
documentation and existing connectors.

The Starter makes it explicit and reproducible.

---

# Consistency across connectors

If ten developers implement ten connectors manually, they will naturally
produce ten different project layouts.

The Starter encourages a common architecture:

- identical project structure;
- identical testing strategy;
- identical configuration conventions;
- identical public contracts.

This consistency benefits both maintainers and contributors.

---

# Documentation by example

Rather than asking developers to read dozens of pages before writing their
first connector, the Starter demonstrates the recommended architecture by
building one.

Generated connectors become living examples of Boomerang best practices.

---

# Developer Experience first

The primary metric of the Starter is not:

- lines of code generated;
- percentage of AI-written code.

The primary metric is:

**Time To First Alert.**

A developer should be able to describe a business need and observe the first
notification only a few minutes later.

---

# Human review remains essential

Generated connectors are intended as first implementations.

They should always be reviewed before production use.

The Starter intentionally optimizes for:

- clarity;
- architectural correctness;
- ease of review;
- extensibility.

It does not attempt to produce fully optimized production code.

---

# Dogfooding

The Starter is developed by building Boomerang's own official connectors.

Every new reference connector is an opportunity to validate and improve the
developer experience.

If the Starter can build Boomerang itself, it can probably build third-party
connectors as well.

---

# Long-term vision

The AI Starter Kit is not meant to replace developers.

Its purpose is to remove repetitive work so developers can focus on business
logic.

The ultimate goal is simple:

Describe a business need.

↓

Review the proposed assumptions.

↓

Run the generated connector.

↓

Receive the first alert.

From that point onward, the connector is yours to review, evolve and maintain.