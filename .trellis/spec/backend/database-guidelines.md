# Database Guidelines

> Database patterns and conventions for this project.

---

## Overview

<!--
Document your project's database conventions here.

Questions to answer:
- What ORM/query library do you use?
- How are migrations managed?
- What are the naming conventions for tables/columns?
- How do you handle transactions?
-->

Primary data stack:

- PostgreSQL for metadata and transaction records
- ChromaDB (MVP) for vector retrieval
- SQLAlchemy 2.x async ORM + Alembic migrations

PostgreSQL is the source of truth. Vector index is rebuildable.

---

## Query Patterns

<!-- How should queries be written? Batch operations? -->

- Use repository methods for all writes; avoid raw SQL in handlers.
- Wrap multi-step metadata updates in one transaction.
- Store `created_at`/`updated_at` in UTC ISO-compatible timestamps.
- Use stable IDs (`document_id`, `chunk_id`) to support idempotent retries.

---

## Migrations

<!-- How to create and run migrations -->

- Create migration:
  - `alembic revision -m "add documents table"`
- Apply migration:
  - `alembic upgrade head`
- Migration files must include reversible `upgrade` and `downgrade`.
- Never modify an applied migration in-place; create a new migration.

---

## Naming Conventions

<!-- Table names, column names, index names -->

- Table names: plural snake_case (`knowledge_bases`, `query_logs`).
- PKs: `id` (UUID or BIGINT, chosen consistently per table set).
- FKs: `<table_singular>_id` (`knowledge_base_id`, `document_id`).
- Unique indexes: `uq_<table>_<columns>`.
- Secondary indexes: `ix_<table>_<columns>`.

---

## Common Mistakes

<!-- Database-related mistakes your team has made -->

- Writing vector index first, metadata second (can leave dangling vectors).
- Using non-deterministic chunk IDs during retries.
- Returning ORM entities directly from API responses.
- Embedding secrets or provider endpoints in code instead of config.
