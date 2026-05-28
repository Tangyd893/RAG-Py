# Logging Guidelines

> How logging is done in this project.

---

## Overview

<!--
Document your project's logging conventions here.

Questions to answer:
- What logging library do you use?
- What are the log levels and when to use each?
- What should be logged?
- What should NOT be logged (PII, secrets)?
-->

Use structured logging with `structlog` across API and worker processes.
All logs must be JSON-serializable and searchable by `request_id` or `job_id`.

---

## Log Levels

<!-- When to use each level: debug, info, warn, error -->

- `debug`: local debugging details, disabled in production by default.
- `info`: normal state transitions (upload accepted, index finished).
- `warn`: recoverable anomalies (retry, fallback, partial results).
- `error`: failed request/task that affects expected outcome.

---

## Structured Logging

<!-- Log format, required fields -->

Required fields:

- `timestamp`
- `level`
- `service` (`api` or `worker`)
- `request_id` (API) or `job_id` (worker)
- `event`
- `error_code` (if failed)
- `latency_ms` (for timed operations)

---

## What to Log

<!-- Important events to log -->

- Indexing lifecycle: `indexing_started`, `chunks_created`, `vector_upserted`, `indexing_finished`.
- Query lifecycle: `query_received`, `retrieval_done`, `llm_completed`.
- External call metrics: provider name, timeout, retry count, token usage.
- Security-relevant events: unauthorized access, rate-limit triggers.

---

## What NOT to Log

<!-- Sensitive data, PII, secrets -->

- API keys, access tokens, passwords, connection strings.
- Raw document content and full user prompt by default.
- PII or sensitive user data unless explicit audited requirement exists.
- Entire exception objects if they include secret-bearing request payloads.
