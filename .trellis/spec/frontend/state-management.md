# State Management

> How state is managed in this project.

---

## Overview

<!--
Document your project's state management conventions here.

Questions to answer:
- What state management solution do you use?
- How is local vs global state decided?
- How do you handle server state?
- What are the patterns for derived state?
-->

State is split by ownership and lifecycle:

- Local UI state: React `useState` / `useReducer`
- Server state: TanStack Query
- Global app state: lightweight store (Zustand) only when needed
- URL state: query parameters for filters/pagination/shareable view state

---

## State Categories

<!-- Local state, global state, server state, URL state -->

- Local state: modal visibility, form draft, transient UI state.
- Global state: auth session, theme, cross-page preferences.
- Server state: knowledge bases, document statuses, query history.
- URL state: table page/sort/filter and selected resource IDs.

---

## When to Use Global State

<!-- Criteria for promoting state to global -->

Promote to global state only when all are true:

1. Needed by 3+ unrelated routes/components
2. Not naturally represented by URL or query cache
3. Requires consistent cross-page persistence

---

## Server State

<!-- How server data is cached and synchronized -->

- Use query keys as canonical identity for server resources.
- Configure retry/timeouts per endpoint criticality.
- Poll indexing job status with capped interval; stop when terminal state reached.
- Cache invalidation must be explicit after document upload/delete operations.

---

## Common Mistakes

<!-- State management mistakes your team has made -->

- Putting API response objects into global store without normalization strategy.
- Duplicating same server data in both Zustand and Query cache.
- Losing filter state on navigation by not syncing to URL.
- Overusing global state for one-page-only concerns.
