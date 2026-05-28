# P0-3 技术设计

## 1. 索引流水线架构

```
Celery Task (index_document)
  → IngestionService.index()
    → Phase 1: parse → DocumentParser.parse(file) → str
    → Phase 2: chunk → TextSplitter.split(text, strategy) → list[ChunkDraft]
    → Phase 3: embed → EmbeddingProvider.embed_texts(contents) → list[vectors]
    → Phase 4: persist → PG insert chunks + Chroma upsert vectors
    → Phase 5: finalize → document.status = indexed
```

每阶段失败时更新 document.error_message 和 indexing_job.error_code。

## 2. Celery 任务 (`app/tasks/indexing.py`)

```python
from app.tasks.celery_app import celery_app

@celery_app.task(
    name="index_document",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def index_document(self, document_id: str):
    # 同步包装：在 Celery task 中运行异步流水线
    import asyncio
    from app.application.services.ingestion_service import IngestionService
    async def _run():
        service = await build_ingestion_service()
        await service.index(UUID(document_id), task_id=self.request.id)
    asyncio.run(_run())
```

### 2.1 Celery conf 从 config 读取

```python
from app.core.config import settings

celery_app.conf.update(
    broker_url=settings.celery_broker_url,
    result_backend=settings.celery_result_backend,
    task_default_queue="indexing",
)
```

## 3. 文档解析器

### 3.1 协议 (`app/infrastructure/parsing/base.py`)

```python
class DocumentParser(Protocol):
    async def parse(self, content: bytes, filename: str) -> str: ...
```

### 3.2 TXT 解析器

```python
class TxtParser:
    async def parse(self, content: bytes, filename: str) -> str:
        return content.decode("utf-8", errors="replace")
```

### 3.3 Markdown 解析器

```python
class MdParser:
    async def parse(self, content: bytes, filename: str) -> str:
        return content.decode("utf-8", errors="replace")
```

### 3.4 解析器路由

根据 `document.content_type` 选择解析器：

| content_type | 解析器 |
|---|---|
| text/plain | TxtParser |
| text/markdown, text/x-markdown | MdParser |
| application/pdf | (P0-3 暂不支持，后续扩展) |

## 4. 文本切分器 (`app/infrastructure/text_splitter/splitter.py`)

```python
class TextSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[ChunkDraft]:
        # 1. 按段落拆分
        # 2. 超长段落按句子拆分
        # 3. 超长句子按字符窗口拆分
        # 4. 相邻 chunk 保持 overlap
        ...
```

### 4.1 ChunkDraft

```python
@dataclass
class ChunkDraft:
    content: str
    chunk_index: int
    token_count: int
    page_number: int | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

## 5. IngestionService (`app/application/services/ingestion_service.py`)

```python
class IngestionService:
    def __init__(self, session, storage, parser, splitter, embedder, vector_store):
        ...

    async def index(self, document_id: UUID, task_id: str):
        # 1. 加载文档和知识库
        # 2. 创建/更新 IndexingJob
        # 3. 幂等清理：删除旧 chunks + 旧向量点
        # 4. 逐阶段执行：
        #    - _phase_parse: 读取文件 → 解析为文本
        #    - _phase_chunk: 文本 → ChunkDraft 列表
        #    - _phase_embed: 文本 → 向量列表
        #    - _phase_persist: 写入 PG + Chroma
        #    - _phase_finalize: 更新状态为 indexed
        # 5. 异常处理：捕获 → 标记 failed → 如果是可重试则 raise

    async def _phase_parse(self, doc, kb):
        doc.status = DocumentStatus.parsing
        ...

    async def _phase_chunk(self, doc, text, kb):
        doc.status = DocumentStatus.chunking
        ...

    async def _phase_embed(self, doc, drafts, kb):
        doc.status = DocumentStatus.embedding
        ...

    async def _phase_persist(self, doc, drafts, vectors):
        # 写入 PG chunks + Chroma vectors
        ...

    async def _phase_finalize(self, doc, job):
        doc.status = DocumentStatus.indexed
        job.status = JobStatus.succeeded
        ...
```

### 5.1 幂等重试

```python
async def _cleanup_previous(self, document_id: UUID):
    # 删除旧 chunks
    await self.session.execute(
        delete(Chunk).where(Chunk.document_id == document_id)
    )
    # 删除旧向量点
    await self.vector_store.delete_by_document(document_id)
```

## 6. BGE Provider 实现

```python
class BgeEmbeddingProvider:
    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "cpu"):
        self.model_name = model_name
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name, device=device)
        self.dimensions = self.model.get_sentence_embedding_dimension()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    async def embed_query(self, query: str) -> list[float]:
        embedding = self.model.encode(query, normalize_embeddings=True)
        return embedding.tolist()
```

> 如 sentence-transformers 不可用，保留占位实现（返回固定维度零向量）。

## 7. Chroma 向量存储 (`app/infrastructure/vector_store/chroma_store.py`)

```python
import chromadb
from chromadb.config import Settings as ChromaSettings

class ChromaVectorStore:
    def __init__(self, host: str, port: int):
        self.client = chromadb.HttpClient(host=host, port=port)

    async def ensure_collection(self, name: str, dimension: int):
        return self.client.get_or_create_collection(
            name=name, metadata={"hnsw:space": "cosine"}
        )

    async def upsert(self, collection_name: str, points: list[VectorPoint]):
        collection = self.client.get_collection(collection_name)
        collection.upsert(
            ids=[p.id for p in points],
            embeddings=[p.vector for p in points],
            metadatas=[p.payload for p in points],
        )

    async def delete_by_document(self, collection_name: str, document_id: str):
        collection = self.client.get_collection(collection_name)
        collection.delete(where={"document_id": document_id})
```

## 8. VectorStore 协议 (`app/infrastructure/vector_store/base.py`)

```python
@dataclass
class VectorPoint:
    id: str
    vector: list[float]
    payload: dict[str, Any]

class VectorStore(Protocol):
    async def ensure_collection(self, name: str, dimension: int) -> Any: ...
    async def upsert(self, collection_name: str, points: list[VectorPoint]) -> None: ...
    async def query(self, collection_name: str, vector: list[float], top_k: int) -> list[VectorPoint]: ...
    async def delete_by_document(self, collection_name: str, document_id: str) -> None: ...
```

## 9. DocumentService 改动

上传成功后触发索引任务：

```python
from app.tasks.indexing import index_document

async def upload(self, ...):
    # ... 现有上传逻辑 ...
    await self.session.flush()

    # 触发异步索引
    index_document.delay(str(doc.id))
    return DocumentUploadResponse(...)
```

## 10. 文件落点汇总

```
[新] app/tasks/indexing.py
[改] app/tasks/celery_app.py
[新] app/application/services/ingestion_service.py
[新] app/infrastructure/parsing/__init__.py
[新] app/infrastructure/parsing/base.py
[新] app/infrastructure/parsing/txt_parser.py
[新] app/infrastructure/parsing/md_parser.py
[新] app/infrastructure/text_splitter/__init__.py
[新] app/infrastructure/text_splitter/splitter.py
[改] app/infrastructure/providers/embedding/bge_provider.py
[新] app/infrastructure/vector_store/__init__.py
[新] app/infrastructure/vector_store/base.py
[新] app/infrastructure/vector_store/chroma_store.py
[改] app/application/services/document_service.py
```
