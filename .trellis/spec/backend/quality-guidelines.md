# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

<!--
Document your project's quality standards here.

Questions to answer:
- What patterns are forbidden?
- What linting rules do you enforce?
- What are your testing requirements?
- What code review standards apply?
-->

Backend quality focuses on correctness, traceability, and provider-agnostic design.

---

## Forbidden Patterns

<!-- Patterns that should never be used and why -->

- Business logic in route handlers.
- Provider SDK calls outside `infrastructure/providers/`.
- Unbounded retries without idempotency keys.
- Hardcoded model/provider names in source code.

---

## Required Patterns

<!-- Patterns that must always be used -->

- Dependency inversion for providers (`EmbeddingProvider`, `LLMProvider` contracts).
- Typed DTOs for API boundaries.
- Stable error codes and request/job correlation IDs.
- Deterministic chunk/vector IDs for reprocessing safety.

---

## Testing Requirements

<!-- What level of testing is expected -->

- Unit tests for domain/application rules are required for each feature.
- Integration tests for repository/provider adapters are required before release.
- At least one end-to-end flow must pass:
  - upload -> index -> query -> sources returned
- Use fake providers (`FakeEmbeddingProvider`, `FakeLLMProvider`) in CI.

---

## Code Review Checklist

<!-- What reviewers should check -->

- Does the change preserve API error contract (`error.code`, `request_id`)?
- Are secrets read from config only?
- Is retry logic idempotent?
- Are logs structured and scrubbed?
- Are tests covering happy path + at least one failure path?
