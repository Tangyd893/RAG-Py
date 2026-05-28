# Quality Guidelines

> Code quality standards for frontend development.

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

Frontend quality standard prioritizes reliable data workflows and maintainable UX for RAG operations.

---

## Forbidden Patterns

<!-- Patterns that should never be used and why -->

- Network calls directly in component render logic.
- Unhandled loading/error/empty states for data views.
- Hardcoded API URLs or model/provider names in page components.
- Large monolithic pages without feature decomposition.

---

## Required Patterns

<!-- Patterns that must always be used -->

- Every async view must show loading, error, and empty states.
- Mutations must provide user feedback (toast/inline status).
- Source citations in answer UI must include document and relevance context.
- Keep component contracts and query hooks strongly typed.

---

## Testing Requirements

<!-- What level of testing is expected -->

- Unit tests for non-trivial hooks and utility formatters.
- Component tests for key interactions (upload, ask, status polling).
- One end-to-end smoke flow:
  - create KB -> upload -> indexed -> ask -> citation shown

---

## Code Review Checklist

<!-- What reviewers should check -->

- Does the UI degrade gracefully on API timeouts and 4xx/5xx?
- Are filters/pagination reflected in URL where applicable?
- Is data-fetching logic isolated in hooks/services?
- Are accessibility basics covered (labels, keyboard, focus)?
- Are critical flows tested?
