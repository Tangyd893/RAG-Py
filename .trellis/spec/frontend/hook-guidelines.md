# Hook Guidelines

> How hooks are used in this project.

---

## Overview

<!--
Document your project's hook conventions here.

Questions to answer:
- What custom hooks do you have?
- How do you handle data fetching?
- What are the naming conventions?
- How do you share stateful logic?
-->

Hooks encapsulate data fetching, mutation flows, and reusable view logic.
Keep hooks deterministic and side-effect aware.

---

## Custom Hook Patterns

<!-- How to create and structure custom hooks -->

- Use one primary concern per hook (`useKnowledgeBaseList`, `useUploadDocument`).
- Return stable API surface: `{ data, isLoading, error, actions }`.
- Place feature hooks under `features/<name>/hooks`; shared hooks under `hooks/`.

---

## Data Fetching

<!-- How data fetching is handled (React Query, SWR, etc.) -->

- Use TanStack Query for server state hooks.
- Query keys must include resource and params (`['documents', kbId, filters]`).
- Mutations should invalidate or update relevant query caches explicitly.

---

## Naming Conventions

<!-- Hook naming rules (use*, etc.) -->

- Hook names start with `use` and use domain terms (`useQueryHistory`).
- File names use `use-<domain>.ts`.
- Prefer `useXxxQuery` / `useXxxMutation` naming when using query library.

---

## Common Mistakes

<!-- Hook-related mistakes your team has made -->

- Calling hooks conditionally.
- Mixing long-lived local UI state and server cache state in same hook.
- Triggering navigation side effects directly inside low-level data hooks.
- Returning unstable objects/functions without memoization where needed.
