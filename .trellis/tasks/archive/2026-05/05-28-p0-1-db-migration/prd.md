# P0-1: 数据库模型与Alembic迁移

## 目标

建立 RAG-Py 系统的核心数据模型，包含全部 7 张 PostgreSQL 表、Alembic 迁移基础设施、异步会话管理和通用仓储基础。

## 需求

### R1: SQLAlchemy 模型

按照 `docs/RAG系统项目架构设计文档.md` 第 4.3 节的表结构，实现以下 ORM 模型：

1. **users** — 用户（含 email、password_hash、role、status）
2. **knowledge_bases** — 知识库（含策略参数 chunk_size/chunk_overlap/retrieval_top_k 等）
3. **documents** — 文档（含 checksum 去重、文件元数据、文档状态）
4. **chunks** — 文本片段（含 content_hash 幂等写入、vector_id 关联向量库）
5. **indexing_jobs** — 索引任务（含进度、尝试次数、错误码）
6. **query_logs** — 查询日志（含 token 用量、延迟、缓存命中）
7. **query_sources** — 查询引用（含 rank、score、关联 chunk）

### R2: 文档状态机（完整版）

状态流转路径：

```text
uploaded → parsing → chunking → embedding → indexed
                 ↘ failed          ↘ failed   ↘ failed
                                          
indexed → deleting → deleted
```

- 每阶段有独立状态值，Worker 可在进度字段外精确区分当前阶段
- 失败可在任意阶段发生，直接转入 `failed`
- 删除是异步流程：`indexed → deleting → deleted`

### R3: Alembic 迁移

- 使用 `alembic` 初始化迁移环境（async 模式）
- 首个迁移包含全部 7 张表的创建、索引和外键
- 迁移必须可逆（upgrade/downgrade）
- 迁移文件遵循命名约定：`alembic revision -m "add initial tables"`

### R4: 异步会话管理

- SQLAlchemy AsyncSession 工厂
- 与 FastAPI 依赖注入集成（`yield` 模式自动回收）
- 配置从 `app.core.config.settings.database_url` 读取

### R5: 通用仓储基础

- `BaseRepository[T]` 泛型基类提供标准 CRUD
- 各实体 Repository 继承基类并添加特化查询
- 写操作封装事务

## 约束

- 使用 SQLAlchemy 2.0 async 风格（`AsyncSession`、`Mapped` 类型注解）
- UUID 由 Python `uuid.uuid4()` 生成，不做 DB 层默认
- 时间字段用 `TIMESTAMPTZ`，默认值为 `now()`
- PostgreSQL 是元数据唯一事实源；向量库数据可重建
- ORM 模型不直接返回给 API 响应（通过 DTO/Schema 转换）

## 验收标准

- [ ] `alembic upgrade head` 执行成功，数据库中可见全部 7 张表及索引
- [ ] `alembic downgrade -1` 可回滚迁移
- [ ] AsyncSession 工厂可正常创建/关闭连接
- [ ] 可对每张表执行 insert/select/update/delete 基础操作
- [ ] 外键约束和唯一约束按预期生效
- [ ] 删除还原并重建迁移流程稳定可复现

## 文件落点

```text
app/infrastructure/db/
├── __init__.py
├── base.py              # declarative_base
├── session.py           # AsyncSession 工厂
├── models.py            # 全部 ORM 模型
├── repository.py        # 通用 BaseRepository
└── migrations/          # Alembic 迁移目录
    ├── env.py
    ├── script.py.mako
    └── versions/
        └── 001_add_initial_tables.py
```

根目录：
- `alembic.ini` — Alembic 主配置
