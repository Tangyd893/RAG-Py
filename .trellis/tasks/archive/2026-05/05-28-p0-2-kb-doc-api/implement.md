# P0-2 实施计划

按依赖顺序的检查清单，每项完成后验证。

---

## Step 1: 基础设施 — Schema + 依赖注入 + 异常处理

- [ ] 1.1 创建 `app/schemas/__init__.py`
- [ ] 1.2 创建 `app/schemas/common.py`（ApiResponse, ErrorDetail, PaginationParams, PaginatedData）
- [ ] 1.3 创建 `app/schemas/knowledge_base.py`（CreateKBRequest, KBResponse, KBDetailResponse）
- [ ] 1.4 创建 `app/schemas/document.py`（DocumentResponse, DocumentUploadResponse）
- [ ] 1.5 扩展 `app/domain/errors.py`（ResourceConflictError）
- [ ] 1.6 创建 `app/api/deps.py`（get_session, get_current_user, get_pagination）
- [ ] 1.7 创建 `app/api/error_handlers.py`（全局异常映射）
- [ ] 1.8 修改 `app/main.py`（注册请求 ID 中间件 + 异常处理器）

**验证**：`python3 -m py_compile` 所有新增文件语法通过。

---

## Step 2: 对象存储抽象

- [ ] 2.1 创建 `app/infrastructure/storage/__init__.py`
- [ ] 2.2 创建 `app/infrastructure/storage/base.py`（ObjectStorage 协议）
- [ ] 2.3 创建 `app/infrastructure/storage/local_storage.py`（LocalStorage 实现）

**验证**：语法编译通过。

---

## Step 3: Repository 扩展

- [ ] 3.1 修改 `app/infrastructure/db/repository.py`
  - 添加 `KnowledgeBaseRepository`（list_by_owner、get_with_stats）
  - 添加 `DocumentRepository`（get_by_kb_and_checksum）

**验证**：语法编译通过。

---

## Step 4: Application Service 层

- [ ] 4.1 创建 `app/application/services/knowledge_base_service.py`
  - `create()` — 校验参数 + 生成 vector_collection + 写入 PG
  - `list_by_user()` — 分页查询
  - `get_detail()` — 含文档统计
- [ ] 4.2 创建 `app/application/services/document_service.py`
  - `upload()` — 校验类型/大小 + checksum + 去重 + 存储 + 写入 PG
  - `get_by_id()` — 查询详情

**验证**：语法编译通过。

---

## Step 5: API 路由

- [ ] 5.1 创建 `app/api/v1/routes/knowledge_bases.py`
  - `POST /knowledge-bases`
  - `GET /knowledge-bases`
  - `GET /knowledge-bases/{kb_id}`
- [ ] 5.2 创建 `app/api/v1/routes/documents.py`
  - `POST /knowledge-bases/{kb_id}/documents`
  - `GET /documents/{document_id}`
- [ ] 5.3 修改 `app/api/v1/__init__.py` 注册新路由

**验证**：语法编译通过。

---

## Step 6: 配置

- [ ] 6.1 修改 `.env.example`（添加 DEV_AUTH_TOKEN 配置项）
- [ ] 6.2 修改 `app/core/config.py`（添加 dev_auth_token 字段）

**验证**：语法编译通过。整个 app 目录无 ImportError（即使无外部依赖也能编译）。

---

## 最终验证清单

- [ ] 全部新增/修改文件语法编译通过
- [ ] `app/schemas/` 存在且能独立 import（语法层面）
- [ ] `app/api/deps.py` 包含 get_session、get_current_user、get_pagination
- [ ] 路由正确挂载到 v1 router
- [ ] 错误处理器映射所有已知领域异常
