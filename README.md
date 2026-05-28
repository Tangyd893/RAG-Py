# RAG-Py

RAG-Py is a RAG backend + Web UI project with:

- FastAPI + Celery backend
- BGE as default embedding provider
- Xiaomi MiMo as default LLM provider (config-driven)
- Docker Compose for middleware and local runtime
- Next.js + Ant Design starter (selected Web UI approach)

## Project Bootstrap (Current)

This repository is in bootstrap stage. Core config files are ready:

- `pyproject.toml`
- `docker-compose.yml`
- `Dockerfile`
- `.env.example`
- `.trellis/spec/*` conventions
- `CONTEXT.md` glossary and shared language
- `docs/开发交接与实现约定.md` handoff rules
- `docs/开发实操指南（你来实现）.md` step-by-step implementation guide

## Quick Start

1. Copy env file:

```bash
cp .env.example .env
```

2. Start middleware and app containers:

```bash
docker compose up --build
```

3. Open service endpoints:

- API: `http://localhost:8000`
- Chroma: `http://localhost:8001`
- Web UI: `http://localhost:3000`

## Selected Web UI Approach (Scheme 3)

Use Next.js + Ant Design starter for synchronous UI development.

Recommended path:

1. Create `web/` app with Next.js (App Router + TypeScript)
2. Install Ant Design and table/form ecosystem
3. Build feature modules in parallel with backend APIs:
   - Knowledge bases
   - Document upload and indexing status
   - Query and source citations

Example initialization commands:

```bash
npx create-next-app@latest web --ts --eslint --src-dir --app --import-alias "@/*"
cd web
npm install antd @ant-design/icons @tanstack/react-query zustand zod axios
```

## Notes

- Do not hardcode model/provider names in business logic.
- Keep all provider settings in config/env.
- Keep PostgreSQL as metadata source of truth; vector data is rebuildable.

## Repository Structure (Scaffold)

```text
RAG-Py/
├── app/                    # backend scaffold
├── web/                    # Next.js + Ant Design scaffold
├── docs/                   # architecture and handoff docs
├── .trellis/               # Trellis workflow/spec/task system
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
└── CONTEXT.md
```
