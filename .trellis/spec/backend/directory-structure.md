# Directory Structure

> How backend code is organized in this project.

---

## Overview

Backend follows a modular monolith layout with clear boundaries:

- `api`: HTTP layer only (routing, request/response schema, auth guard)
- `application`: use-case orchestration and transaction boundaries
- `domain`: business rules, entities, and service contracts
- `infrastructure`: integrations (DB, vector store, LLM, embedding, storage)
- `tasks`: asynchronous indexing and maintenance jobs

No infrastructure SDK call should appear in `domain`.

---

## Directory Layout

```text
app/
├── main.py
├── api/
│   └── v1/
│       ├── health.py
│       ├── knowledge_bases.py
│       ├── documents.py
│       └── queries.py
├── application/
│   ├── services/
│   └── dto/
├── domain/
│   ├── models/
│   ├── repositories/
│   ├── errors.py
│   └── types.py
├── infrastructure/
│   ├── db/
│   ├── vector_store/
│   ├── providers/
│   │   ├── embedding/
│   │   │   └── bge_provider.py
│   │   └── llm/
│   │       └── mimo_provider.py
│   ├── storage/
│   └── observability/
├── tasks/
│   ├── celery_app.py
│   └── indexing.py
└── core/
    ├── config.py
    ├── logging.py
    └── errors.py
```

---

## Module Organization

- Add new business capability in vertical slices: `api -> application -> domain -> infrastructure`.
- Place provider-specific logic under `infrastructure/providers/*`.
- Keep API layer thin; request parsing and response shaping only.
- Put cross-cutting concerns in `core/` (config, logging, error mapping, constants).

---

## Naming Conventions

- Use `snake_case` for Python files and directories.
- Name service modules as `<context>_service.py`.
- Name provider adapters as `<provider>_<capability>.py` (example: `mimo_llm.py`).
- API route modules use plural nouns (`knowledge_bases.py`, `documents.py`).

---

## Examples

- `infrastructure/providers/embedding/bge_provider.py`: BGE embedding adapter.
- `infrastructure/providers/llm/mimo_provider.py`: Xiaomi MiMo LLM adapter.
- `tasks/indexing.py`: async indexing pipeline entry.
