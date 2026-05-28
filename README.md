# RAG-Py

RAG-Py is a RAG backend + Web UI project with:

- FastAPI + Celery backend
- BGE as default embedding provider
- Xiaomi MiMo as default LLM provider (config-driven)
- Docker Compose for middleware and local runtime
- Next.js + Ant Design starter (selected Web UI approach)

## Project Status (Current)

P0 后端核心 + P1 Web UI 已实现：

- ✅ **P0-1**: 数据库模型（7 表）+ Alembic 迁移
- ✅ **P0-2**: 知识库 CRUD + 文档上传 API（含去重/鉴权/对象存储）
- ✅ **P0-3**: 异步索引流水线（解析→分块→BGE→Chroma）
- ✅ **P0-4**: RAG 查询链路（检索→Prompt→MiMo→持久化→来源引用）
- ✅ **P1**: Web UI 三条主流程（知识库管理、文档上传、智能问答）
- ✅ **P2**: 检索优化（BM25 混合检索 + RRF 融合 + BGE 重排 + 评测框架）

待完成：
- ⬜ 测试与可观测性补齐
- ⬜ MiMo/BGE 实际 API 调试验证（代码已就绪，待配置真实端点）
- ⬜ PDF/DOCX 解析器
- ⬜ 流式查询接口（SSE）

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

## Repository Structure

```text
RAG-Py/
├── app/
│   ├── main.py                         # FastAPI 入口 + 中间件
│   ├── api/
│   │   ├── deps.py                      # 依赖注入（会话/鉴权/分页）
│   │   ├── error_handlers.py            # 全局异常映射
│   │   └── v1/routes/
│   │       ├── health.py                # 健康检查
│   │       ├── knowledge_bases.py       # 知识库 CRUD
│   │       ├── documents.py             # 文档上传/查询
│   │       └── queries.py               # RAG 查询
│   ├── application/services/
│   │   ├── knowledge_base_service.py    # 知识库用例
│   │   ├── document_service.py          # 文档上传/去重
│   │   ├── ingestion_service.py         # 索引流水线编排
│   │   ├── rag_service.py               # RAG 查询编排
│   │   ├── retrieval_service.py         # 向量检索
│   │   └── prompt_builder.py            # Prompt 构建
│   ├── domain/
│   │   └── errors.py                    # 领域异常
│   ├── infrastructure/
│   │   ├── db/                          # SQLAlchemy + Alembic
│   │   ├── storage/                     # 对象存储抽象 + 本地实现
│   │   ├── parsing/                     # 文档解析器（TXT/MD）
│   │   ├── text_splitter/               # 层级文本切分器
│   │   ├── vector_store/                # 向量存储抽象 + Chroma
│   │   └── providers/
│   │       ├── embedding/               # BGE 向量化
│   │       └── llm/                     # LLM 协议 + MiMo
│   ├── tasks/
│   │   ├── celery_app.py                # Celery 配置
│   │   └── indexing.py                  # 异步索引任务
│   ├── schemas/                         # Pydantic 请求/响应模型
│   └── core/
│       ├── config.py                    # 全局配置
│       └── logging.py                   # 结构化日志
├── web/                                 # Next.js + Ant Design 脚手架
├── docs/                                # 架构文档
├── docker-compose.yml
└── pyproject.toml
```
