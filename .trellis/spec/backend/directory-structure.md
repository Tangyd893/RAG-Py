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
├── main.py                         # FastAPI 入口 + CORS + 请求ID中间件 + 异常处理
├── api/
│   ├── deps.py                      # 依赖注入：get_session、get_current_user、get_pagination
│   ├── error_handlers.py            # 领域异常 → HTTP 状态码映射
│   └── v1/
│       ├── __init__.py              # v1 路由器注册
│       └── routes/
│           ├── health.py            # /health /health/ready
│           ├── knowledge_bases.py   # 知识库 CRUD
│           ├── documents.py         # 文档上传 / 详情查询
│           └── queries.py           # RAG 查询
├── application/
│   └── services/
│       ├── knowledge_base_service.py    # 知识库创建/列表/详情（含统计）
│       ├── document_service.py          # 文档上传/checksum去重/类型校验
│       ├── ingestion_service.py         # 索引流水线（5阶段编排+幂等清理）
│       ├── rag_service.py               # RAG 查询编排（检索→Prompt→LLM→持久化）
│       ├── retrieval_service.py         # Query向量化 + Chroma检索 + 结果过滤
│       └── prompt_builder.py            # 系统提示词 + 上下文格式化
├── domain/
│   └── errors.py                    # DomainError、ResourceNotFound、ValidationFailed、ResourceConflict
├── infrastructure/
│   ├── db/                          # SQLAlchemy ORM + Alembic migrations
│   │   ├── base.py                  # DeclarativeBase + TimestampMixin + new_uuid
│   │   ├── models.py                # 7 张表 ORM 模型
│   │   ├── session.py               # AsyncSession 工厂 + get_session 依赖
│   │   ├── repository.py            # BaseRepository + KnowledgeBaseRepository + DocumentRepository
│   │   └── migrations/              # Alembic 环境 + 迁移文件
│   ├── storage/                     # 对象存储
│   │   ├── base.py                  # ObjectStorage 协议
│   │   └── local_storage.py         # 本地文件存储实现
│   ├── parsing/                     # 文档解析
│   │   ├── base.py                  # DocumentParser 协议
│   │   ├── txt_parser.py            # TXT 解析器
│   │   └── md_parser.py             # Markdown 解析器
│   ├── text_splitter/               # 文本切分
│   │   └── splitter.py              # 层级切分器（段落→句子→字符窗口）
│   ├── vector_store/                # 向量存储
│   │   ├── base.py                  # VectorStore 协议 + VectorPoint
│   │   └── chroma_store.py          # ChromaDB HTTP 适配器
│   └── providers/
│       ├── embedding/
│       │   └── bge_provider.py      # BGE 嵌入模型（真实调用+占位回退）
│       └── llm/
│           ├── base.py              # LLMProvider 协议 + GenerationResult
│           └── mimo_provider.py     # MiMo HTTP API 适配器
├── schemas/                         # Pydantic 请求/响应
│   ├── common.py                    # ApiResponse、ErrorDetail、PaginationParams、PaginatedData
│   ├── knowledge_base.py            # CreateKBRequest、KBResponse、KBDetailResponse
│   ├── document.py                  # DocumentResponse、DocumentUploadResponse
│   └── query.py                     # QueryRequest、QueryResponse、SourceResponse、UsageInfo
├── tasks/
│   ├── celery_app.py                # Celery 应用配置（broker/backend 从 config 读取）
│   └── indexing.py                  # index_document 异步任务
└── core/
    ├── config.py                    # Pydantic Settings（.env 驱动）
    └── logging.py                   # structlog 结构化日志配置
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
