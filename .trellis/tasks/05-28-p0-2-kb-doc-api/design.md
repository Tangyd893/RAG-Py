# P0-2 技术设计

## 1. Pydantic Schema 层

### 1.1 通用响应包装 (`app/schemas/common.py`)

```python
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

TData = TypeVar("TData")

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None

class ApiResponse(BaseModel, Generic[TData]):
    data: Optional[TData] = None
    error: Optional[ErrorDetail] = None
    request_id: str

class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

class PaginatedData(BaseModel, Generic[TData]):
    items: list[TData]
    total: int
    page: int
    page_size: int
```

### 1.2 知识库 Schemas (`app/schemas/knowledge_base.py`)

```python
class CreateKBRequest(BaseModel):
    name: str
    description: Optional[str] = None
    chunk_size: int = 500
    chunk_overlap: int = 50
    retrieval_top_k: int = 5

class KBResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    embedding_model: str
    vector_collection: str
    chunk_size: int
    chunk_overlap: int
    retrieval_top_k: int
    status: str
    created_at: str
    updated_at: str

class KBDetailResponse(KBResponse):
    document_count: int = 0
    indexed_count: int = 0
    failed_count: int = 0
```

### 1.3 文档 Schemas (`app/schemas/document.py`)

```python
class DocumentResponse(BaseModel):
    id: str
    knowledge_base_id: str
    filename: str
    content_type: str
    file_size: int
    checksum: str
    status: str
    error_message: Optional[str]
    created_at: str
    updated_at: str

class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str
    duplicate: bool = False
```

## 2. 鉴权设计 (`app/api/deps.py`)

### 2.1 开发模式鉴权（MVP）

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.infrastructure.db.session import get_session
from app.infrastructure.db.models import User

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    # 开发模式：检查 DEV_AUTH_TOKEN
    if not hasattr(settings, 'dev_auth_token') or not settings.dev_auth_token:
        return None  # 无鉴权模式
    if not credentials or credentials.credentials != settings.dev_auth_token:
        raise HTTPException(status_code=401, detail="UNAUTHORIZED")
    # 查找或创建设置用户
    user = await session.execute(select(User).where(User.email == "dev@rag.local"))
    user = user.scalar_one_or_none()
    if not user:
        user = User(email="dev@rag.local")
        session.add(user)
        await session.flush()
    return user
```

逻辑：
1. 如果未配置 `DEV_AUTH_TOKEN` → 跳过鉴权，`current_user=None`
2. 如果配置了 → 校验 Bearer token，创建默认开发用户

## 3. Application Service 层

### 3.1 KnowledgeBaseService

```python
class KnowledgeBaseService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.kb_repo = KnowledgeBaseRepository(session)

    async def create(self, user_id: UUID, cmd: CreateKBCommand) -> KnowledgeBase:
        # 1. 校验 chunk_size/chunk_overlap
        # 2. 生成 vector_collection = f"kb_{id}_{model_hash}"
        # 3. 创建 KnowledgeBase 实体
        # 4. 返回

    async def list_by_user(self, user_id: UUID, pagination: PaginationParams) -> PaginatedResult[KnowledgeBase]:
        ...

    async def get_by_id(self, kb_id: UUID, user_id: UUID) -> KnowledgeBase:
        # 含权限检查 + 文档统计
        ...
```

### 3.2 DocumentService

```python
class DocumentService:
    def __init__(self, session: AsyncSession, storage: ObjectStorage):
        self.session = session
        self.storage = storage

    async def upload(self, kb_id: UUID, user_id: UUID, file: UploadFile) -> Document:
        # 1. 校验文件类型和大小
        # 2. 计算 SHA256 checksum
        # 3. checksum 去重检查（同 KB）
        # 4. 写入对象存储
        # 5. 创建 Document 记录 (status=uploaded)
        # 6. 返回

    async def get_by_id(self, doc_id: UUID) -> Document:
        ...
```

### 3.3 Checksum 去重逻辑

```python
async def _check_duplicate(self, kb_id: UUID, checksum: str) -> Optional[Document]:
    existing = await self.session.execute(
        select(Document).where(
            Document.knowledge_base_id == kb_id,
            Document.checksum == checksum,
        )
    )
    doc = existing.scalar_one_or_none()
    if not doc:
        return None  # 非重复
    if doc.status == DocumentStatus.indexed:
        return doc  # 已索引，直接返回
    if doc.status == DocumentStatus.failed:
        return None  # 失败可重试
    return doc  # 处理中，返回当前状态
```

## 4. 对象存储抽象

### 4.1 接口 (`app/infrastructure/storage/base.py`)

```python
from typing import Protocol, BinaryIO

class ObjectStorage(Protocol):
    async def put(self, key: str, data: bytes) -> str: ...
    async def get(self, key: str) -> Optional[bytes]: ...
    async def delete(self, key: str) -> None: ...
```

### 4.2 本地实现 (`app/infrastructure/storage/local_storage.py`)

```python
class LocalStorage:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def put(self, key: str, data: bytes) -> str:
        path = self.base_dir / key
        path.write_bytes(data)
        return str(path)

    async def get(self, key: str) -> Optional[bytes]:
        path = self.base_dir / key
        return path.read_bytes() if path.exists() else None

    async def delete(self, key: str) -> None:
        path = self.base_dir / key
        path.unlink(missing_ok=True)
```

## 5. 领域异常扩展

在 `app/domain/errors.py` 中添加：

```python
class ResourceConflictError(DomainError):
    def __init__(self, message: str, code: str = "RESOURCE_CONFLICT"):
        super().__init__(message, code=code)
```

## 6. 路由设计

### 6.1 knowledge_bases.py

```python
router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])

@router.post("")
async def create_kb(
    body: CreateKBRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    ...

@router.get("")
async def list_kbs(
    pagination: PaginationParams = Depends(),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    ...

@router.get("/{kb_id}")
async def get_kb(kb_id: UUID, ...):
    ...
```

### 6.2 documents.py

```python
router = APIRouter(prefix="/knowledge-bases/{kb_id}/documents", tags=["documents"])

@router.post("")
async def upload_document(
    kb_id: UUID,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    ...

@router.get("/{document_id}")
async def get_document(document_id: UUID, ...):
    ...
```

### 6.3 错误处理（全局异常映射）

在 `app/api/error_handlers.py` 中注册 FastAPI exception handlers：

| 领域异常 | HTTP | error.code |
|---------|------|------------|
| `ValidationFailedError` | 422 | `VALIDATION_FAILED` |
| `ResourceNotFoundError` | 404 | 根据上下文 |
| `ResourceConflictError` | 409 | `DUPLICATE_DOCUMENT` |

## 7. 请求 ID 中间件

在 `app/main.py` 中注册中间件：
- 从请求头 `X-Request-ID` 读取，若无则生成 `req_{uuid_short}`
- 注入到 structlog 上下文
- 附加到响应头

## 8. 知识库 Repository

```python
class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, KnowledgeBase)

    async def list_by_owner(self, owner_id: UUID, offset: int, limit: int) -> tuple[list[KnowledgeBase], int]:
        # COUNT + LIMIT/OFFSET 查询
        ...

    async def get_with_stats(self, kb_id: UUID) -> tuple[KnowledgeBase, dict]:
        # 联查文档状态统计
        ...
```

## 9. 文件落点汇总

```
app/schemas/__init__.py                # 空
app/schemas/common.py                  # ApiResponse, PaginationParams
app/schemas/knowledge_base.py          # CreateKBRequest, KBResponse, KBDetailResponse
app/schemas/document.py                # DocumentResponse, DocumentUploadResponse

app/api/deps.py                        # get_session, get_current_user, get_pagination
app/api/error_handlers.py              # 全局异常映射
app/api/v1/routes/knowledge_bases.py   # KB CRUD 路由
app/api/v1/routes/documents.py         # 文档上传/查询路由

app/application/services/knowledge_base_service.py
app/application/services/document_service.py

app/infrastructure/storage/__init__.py
app/infrastructure/storage/base.py     # ObjectStorage 协议
app/infrastructure/storage/local_storage.py

app/infrastructure/db/repository.py    [改] 添加 KnowledgeBaseRepository, DocumentRepository

app/domain/errors.py                   [改] 添加 ResourceConflictError

app/api/v1/__init__.py                 [改] 注册新路由
app/main.py                            [改] 添加中间件和异常处理器
```
