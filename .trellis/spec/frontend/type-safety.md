# Type Safety

> Type safety patterns in this project.

---

## Overview

<!--
Document your project's type safety conventions here.

Questions to answer:
- What type system do you use?
- How are types organized?
- What validation library do you use?
- How do you handle type inference?
-->

Frontend is strict TypeScript-first. Runtime validation is required at API boundaries.

---

## Type Organization

<!-- Where types are defined, shared types vs local types -->

- Shared DTO/contracts go in `types/contracts/`.
- Feature-specific view models stay near feature modules.
- Do not import backend ORM/entity types into UI.

---

## Validation

<!-- Runtime validation patterns (Zod, Yup, io-ts, etc.) -->

- Validate external API payloads with `zod` schemas before use in critical flows.
- Derive static types from schemas (`z.infer`) to avoid drift.
- Fail fast on malformed response shape with safe fallback UI.

---

## Common Patterns

<!-- Type utilities, generics, type guards -->

- Prefer discriminated unions for async states (`idle/loading/success/error`).
- Use `Readonly` and utility types for immutable props where relevant.
- Model provider and config selections as string literal unions.

---

## Forbidden Patterns

<!-- any, type assertions, etc. -->

- Bare `any` or `as any` outside isolated migration shims.
- Blind non-null assertions (`!`) on async data.
- Duplicating string enums without shared source.
- Ignoring backend contract changes without schema updates.
