# P0-3: 索引链路（异步）

## 目标

实现文档异步索引流水线：解析 → 分块 → 向量化 → 入库，支持 Celery 任务调度、幂等重试和文档状态流转。

## 需求

### R1: Celery 索引任务

- 任务入口：`index_document(document_id: str)`
- 自动重试：TransientProviderError、RedisError 等可重试异常（最多 3 次，指数退避）
- 不可重试错误直接标记文档为 `failed`
- 任务从 `app.core.config.settings` 读取 broker/backend 配置

### R2: 文档解析器

- 实现 `DocumentParser` 协议接口
- MVP 支持 TXT 和 MD 格式
- `TxtParser`：直接读取文本内容
- `MdParser`：读取 Markdown 文本
- 后续扩展 PDF、DOCX

### R3: 文本切分器

- 实现 `TextSplitter` 层级分块：
  1. 按段落拆分（`\n\n`）
  2. 段落超长按句子拆分（`。！？\n`）
  3. 句子仍超长按字符窗口拆分
- 相邻 chunk 保持 `chunk_overlap` 重叠
- 参数从知识库策略读取（chunk_size、chunk_overlap）
- 输出 `ChunkDraft` 列表

### R4: IngestionService 编排

- 分阶段执行：parse → chunk → embed → persist → finalize
- 每阶段更新文档状态（parsing/chunking/embedding/indexed）
- 阶段失败记录错误码，文档进入 `failed`
- 重试时清理旧 chunk 和向量点（幂等）
- 向量写入使用 `vector_id = chunk_{chunk.id}` 确保稳定

### R5: BGE 向量化接入

- 实现 `BgeEmbeddingProvider` 真实调用
- 支持批量文本向量化
- 记录模型名称、维度、耗时
- 嵌入缓存：`embedding:bge:{sha256(text)}`

### R6: Chroma 向量存储

- 实现 `ChromaVectorStore` 适配器
- 按知识库隔离 collection（kb_{id}_{model_hash}）
- 支持 upsert（幂等）、query（检索）、delete
- collection 在知识库创建时初始化

## 约束

- 索引任务在 Worker 中异步执行，不阻塞 API
- 分块和向量写入必须幂等（基于 content_hash 和稳定 vector_id）
- 向量库数据可从 PostgreSQL 重建
- Provider 调用不在 domain 层
- 文件读取通过 ObjectStorage 接口

## 验收标准

- [ ] 上传 TXT/MD 文档后，Celery 自动触发索引
- [ ] 文档状态按 uploaded → parsing → chunking → embedding → indexed 流转
- [ ] 索引成功后在 chunks 表和 Chroma 中可见数据
- [ ] 解析失败文档进入 `failed`，错误码和消息持久化
- [ ] 重试不产生重复 chunks（幂等验证）
- [ ] Chroma collection 正确隔离（每 KB 一个）
- [ ] 索引进度在 indexing_jobs 表中更新

## 文件落点

```
app/tasks/
├── __init__.py
├── celery_app.py          [改] 从 config 读取 broker/backend
└── indexing.py            [新] 索引任务入口

app/application/services/
└── ingestion_service.py   [新] 索引流水线编排

app/infrastructure/parsing/
├── __init__.py
├── base.py                [新] DocumentParser 协议
├── txt_parser.py          [新] TXT 解析器
└── md_parser.py           [新] MD 解析器

app/infrastructure/text_splitter/
├── __init__.py
└── splitter.py            [新] 层级文本切分器

app/infrastructure/providers/embedding/
└── bge_provider.py        [改] 实现真实 BGE 调用

app/infrastructure/vector_store/
├── __init__.py
├── base.py                [新] VectorStore 协议
└── chroma_store.py        [新] Chroma 适配器

app/application/services/
└── document_service.py    [改] 上传后触发索引任务
```
