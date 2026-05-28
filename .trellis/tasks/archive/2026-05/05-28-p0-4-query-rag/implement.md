# P0-4 实施计划

---

## Step 1: Schema + LLM 协议

- [ ] 1.1 创建 `app/schemas/query.py`（QueryRequest/QueryResponse/SourceResponse/UsageInfo）
- [ ] 1.2 创建 `app/infrastructure/providers/llm/base.py`（LLMProvider 协议 + GenerationResult）
- [ ] 1.3 修改 `app/infrastructure/providers/llm/mimo_provider.py`（真实 HTTP 调用）

**验证**：语法编译通过。

---

## Step 2: 检索 + Prompt 构建

- [ ] 2.1 创建 `app/application/services/retrieval_service.py`（向量检索 + 过滤）
- [ ] 2.2 创建 `app/application/services/prompt_builder.py`（系统提示词 + 上下文格式）

**验证**：语法编译通过。

---

## Step 3: RAGService 重写

- [ ] 3.1 重写 `app/application/services/rag_service.py`
  - `query()` — 主编排：检索 → Prompt → LLM → 持久化
  - `_persist()` — 写入 query_logs + query_sources
  - `_to_response()` — 构建 QueryResponse

**验证**：语法编译通过。

---

## Step 4: 查询路由

- [ ] 4.1 创建 `app/api/v1/routes/queries.py`
  - `POST /queries`
- [ ] 4.2 修改 `app/api/v1/__init__.py` 注册查询路由

**验证**：语法编译通过。全量 app/*.py 语法检查。

---

## 最终验证清单

- [ ] 全部新增/修改文件语法编译通过
- [ ] RAG 流水线：检索 → Prompt → LLM → 持久化
- [ ] 空结果返回明确说明
- [ ] sources 含完整字段
- [ ] query_logs + query_sources 正确持久化
- [ ] 所有注释和文档字符串使用简体中文
