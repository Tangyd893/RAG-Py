# P0-1 技术设计

## 1. ORM 模型设计

### 1.1 基类

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func
from datetime import datetime

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

### 1.2 表关系图

```
users ──→ knowledge_bases ──→ documents ──→ chunks
  │              │                  │              │
  │              │                  │              │
  └────── query_logs ←──────────────┘              │
                │                                  │
                └──── query_sources ←──────────────┘
                         (chunk 引用可选)
```

### 1.3 状态枚举

```python
class UserStatus(str, enum.Enum):
    active = "active"
    disabled = "disabled"

class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"

class KBStatus(str, enum.Enum):
    active = "active"
    archived = "archived"

class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    parsing = "parsing"
    chunking = "chunking"
    embedding = "embedding"
    indexed = "indexed"
    failed = "failed"
    deleting = "deleting"
    deleted = "deleted"

class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"

class QueryStatus(str, enum.Enum):
    succeeded = "succeeded"
    failed = "failed"
```

### 1.4 模型字段映射（严格遵循架构文档第 4.3 节 SQL）

以 `documents` 表为例：

| DB 列 | Python 属性 | 类型 | 约束 |
|-------|------------|------|------|
| id | id | UUID | PK, default=uuid4 |
| knowledge_base_id | knowledge_base_id | UUID | FK → knowledge_bases.id |
| uploader_id | uploader_id | UUID | FK → users.id |
| filename | filename | String(512) | NOT NULL |
| content_type | content_type | String(128) | NOT NULL |
| object_key | object_key | Text | NOT NULL |
| file_size | file_size | BigInteger | NOT NULL |
| checksum | checksum | CHAR(64) | NOT NULL |
| parser_name | parser_name | String(128) | nullable |
| page_count | page_count | Integer | nullable |
| status | status | String(32) | default="uploaded" |
| error_message | error_message | Text | nullable |
| created_at | created_at | TIMESTAMPTZ | server_default=now() |
| updated_at | updated_at | TIMESTAMPTZ | server_default=now() |

唯一约束：`UNIQUE(knowledge_base_id, checksum)` — 同 KB 内相同文件去重。

## 2. 表间关系（ORM relationship）

| 源 | 目标 | 关系 |
|----|------|------|
| knowledge_bases | documents | 1:N, back_populates |
| knowledge_bases | chunks | 1:N（冗余字段便于过滤） |
| documents | chunks | 1:N, cascade="all, delete-orphan" |
| documents | indexing_jobs | 1:N, cascade="all, delete-orphan" |
| knowledge_bases | query_logs | 1:N |
| query_logs | query_sources | 1:N, cascade="all, delete-orphan" |
| chunks | query_sources | 1:N（optional，chunk 可能被删除后保留引用） |

## 3. Alembic 迁移配置

### 3.1 初始化命令

```bash
cd app/infrastructure/db
alembic init -t async migrations
```

迁移目录放在 `app/infrastructure/db/migrations/`，`alembic.ini` 放在项目根目录。

### 3.2 env.py 关键配置

```python
from app.infrastructure.db.base import Base
from app.infrastructure.db.models import *  # 确保所有模型被导入
from app.core.config import settings

target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", settings.database_url)
```

### 3.3 alembic.ini

```ini
[alembic]
script_location = app/infrastructure/db/migrations
sqlalchemy.url = postgresql+asyncpg://rag:rag@localhost:5432/rag

[loggers]
keys = root,sqlalchemy,alembic
...
```

## 4. 会话管理

### 4.1 session.py

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
```

`get_session` 作为 FastAPI 依赖项使用（`Depends(get_session)`）。

## 5. 通用仓储

### 5.1 BaseRepository

```python
from typing import Generic, TypeVar, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    async def get(self, id: UUID) -> T | None:
        return await self.session.get(self.model, id)

    async def add(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: T) -> None:
        await self.session.delete(entity)
        await self.session.flush()
```

各实体 Repository 继承并添加特化查询方法（如 `DocumentRepository.get_by_kb_id`）。

## 6. 文件落点汇总

```
（项目根）/alembic.ini
app/infrastructure/db/__init__.py       # 包标识
app/infrastructure/db/base.py           # Base + TimestampMixin
app/infrastructure/db/models.py         # 全部 7 张表 ORM
app/infrastructure/db/session.py        # engine + async_session + get_session
app/infrastructure/db/repository.py     # BaseRepository
app/infrastructure/db/migrations/       # Alembic
├── env.py
├── script.py.mako
└── versions/
    └── 001_add_initial_tables.py
```
