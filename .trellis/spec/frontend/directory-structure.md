# Directory Structure

> How frontend code is organized in this project.

---

## Overview

<!--
Document your project's frontend directory structure here.

Questions to answer:
- Where do components live?
- How are features/modules organized?
- Where are shared utilities?
- How are assets organized?
-->

Frontend is a Next.js + React TypeScript admin-style Web UI for RAG operations.
UI should be feature-oriented, not purely component-type oriented.

---

## Directory Layout

```text
web/
├── src/
│   ├── app/
│   │   ├── (dashboard)/
│   │   ├── login/
│   │   └── layout.tsx
│   ├── features/
│   │   ├── knowledge-bases/
│   │   ├── documents/
│   │   ├── queries/
│   │   └── settings/
│   ├── components/
│   │   ├── common/
│   │   └── charts/
│   ├── hooks/
│   ├── services/
│   │   ├── api-client.ts
│   │   └── endpoints/
│   ├── stores/
│   ├── types/
│   ├── styles/
│   └── config/
│       └── runtime.ts
└── public/
```

---

## Module Organization

<!-- How should new features be organized? -->

- Feature modules own their pages, API calls, and local components.
- `components/common` only holds truly reusable presentational components.
- API contract types belong to `types/contracts`.
- Runtime flags and provider metadata come from `config/runtime.ts`.

---

## Naming Conventions

<!-- File and folder naming rules -->

- Use `kebab-case` for folders and files.
- React components use `PascalCase` export names.
- Hook files use `use-*.ts` naming and `use*` function names.
- Avoid ambiguous names like `utils.ts`; prefer domain names.

---

## Examples

<!-- Link to well-organized modules as examples -->

- `features/knowledge-bases/*`: KB list/create/detail flows.
- `features/documents/*`: upload, status, and delete workflows.
- `features/queries/*`: ask question and source rendering.
