# P0-2: 知识库与文档上传 API

## 目标

实现知识库 CRUD 和文档上传接口，包含 checksum 去重、本地对象存储适配器、统一错误响应和开发模式鉴权。

## 需求

### R1: 知识库接口

- `POST /api/v1/knowledge-bases` — 创建知识库
  - 输入：name（必填）、description（可选）、chunk_size/chunk_overlap/retrieval_top_k（可选，有默认值）
  - 校验：chunk_size 200-1500，chunk_overlap < chunk_size/2
  - 自动生成 vector_collection（格式 `kb_{id}_{model_hash}`）
  - embedding_model 从配置读取默认值
  - 响应：知识库 ID、名称、状态、collection 名、创建时间

- `GET /api/v1/knowledge-bases` — 知识库列表
  - 分页参数：page（默认 1）、page_size（默认 20）
  - 返回当前用户拥有的知识库

- `GET /api/v1/knowledge-bases/{kb_id}` — 知识库详情
  - 含文档数量和状态统计

### R2: 文档上传接口

- `POST /api/v1/knowledge-bases/{kb_id}/documents` — 上传文档
  - multipart/form-data，字段：file（必填）
  - 支持格式：TXT、MD、PDF、DOCX
  - 文件大小限制：50MB
  - 计算 SHA256 checksum
  - 同 KB 内 checksum 去重：
    - 已 indexed 的重复文件 → 返回已有文档（duplicate=true）
    - 已 failed 的重复文件 → 允许重新上传
    - 正在处理中的重复文件 → 返回当前状态
  - 写入本地对象存储（路径 `{uuid}.bin`）
  - 创建 Document 记录（status=uploaded）
  - P0-2 不触发索引任务（留给 P0-3）

### R3: 文档详情接口

- `GET /api/v1/documents/{document_id}` — 文档详情
  - 返回文档元数据、状态、错误信息、chunk 统计

### R4: 统一错误响应

- 所有响应包装格式：`{"data": ..., "error": null, "request_id": "..."}`
- 每个请求生成或透传 `X-Request-ID`
- 错误对象：`{"code": "ERROR_CODE", "message": "...", "details": {}}`

### R5: 开发模式鉴权

- 通过 `DEV_AUTH_TOKEN` 环境变量启用
- 请求携带 `Authorization: Bearer <token>`
- 内置默认用户（email=dev@rag.local），首次访问自动创建
- `get_current_user` 作为 FastAPI 依赖注入

### R6: 对象存储抽象

- `ObjectStorage` 接口：`put(key, data)` / `get(key)` / `delete(key)`
- MVP 实现 `LocalStorage`（存储到 `{LOCAL_STORAGE_PATH}/{key}`）
- 接口与实现分离，便于后续替换为 MinIO/S3

## 约束

- 路由不直接访问 ORM 或对象存储，通过 Application Service 编排
- API 响应不直接返回 ORM 模型，通过 Pydantic Schema 转换
- 配置全部来自 `app.core.config.settings`
- 文件名为展示字段，存储路径使用 UUID
- SHA256 checksum 使用 Python `hashlib.sha256`

## 验收标准

- [ ] `POST /api/v1/knowledge-bases` 创建成功，PG 中可见记录
- [ ] `GET /api/v1/knowledge-bases` 返回分页列表
- [ ] `GET /api/v1/knowledge-bases/{kb_id}` 返回详情含统计
- [ ] `POST /api/v1/knowledge-bases/{kb_id}/documents` 上传 TXT/MD 成功
- [ ] 同 KB 重复上传同一文件返回已有记录（duplicate=true）
- [ ] 不支持的文件类型返回 `UNSUPPORTED_FILE_TYPE`
- [ ] 文件大小超限返回错误
- [ ] 所有错误响应包含 `error.code` 和 `request_id`
- [ ] `chunk_size` 超出范围返回 `VALIDATION_FAILED`
- [ ] 未认证请求返回 `UNAUTHORIZED`（开发模式下）

## 文件落点

```
app/schemas/
├── __init__.py
├── common.py              # ApiResponse, ErrorResponse, PaginationParams
├── knowledge_base.py      # CreateKBRequest, KBResponse
└── document.py            # DocumentResponse

app/api/
├── deps.py                # get_session, get_current_user, get_pagination

app/api/v1/routes/
├── knowledge_bases.py     # KB 路由
└── documents.py           # 文档路由

app/application/services/
├── knowledge_base_service.py
└── document_service.py

app/infrastructure/storage/
├── __init__.py
├── base.py                # ObjectStorage 协议
└── local_storage.py       # 本地文件存储

app/domain/errors.py       [改] 扩展领域异常
```
