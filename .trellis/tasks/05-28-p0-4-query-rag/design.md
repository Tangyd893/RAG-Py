# P0-4 技术设计

## 1. 查询流水线架构

```
POST /api/v1/queries
  → RAGService.query()
    → 1. 权限检查 (assert KB access)
    → 2. Retrieve: BGE 向量检索 → top_k * 3 → 过滤 → 取 top_k
    → 3. Prompt: 构建 system + user messages
    → 4. Generate: 调用 MiMo LLM
    → 5. Persist: query_logs + query_sources
    → 6. Response: answer + sources + usage + latency
```

## 2. Schema (`app/schemas/query.py`)

```python
class QueryRequest(BaseModel):
    knowledge_base_id: str
    question: str
    top_k: int = 5
    temperature: float = 0.2

class SourceResponse(BaseModel):
    source_id: str
    document_id: str
    chunk_id: str
    filename: str
    page_number: int | None
    score: float
    content: str

class UsageInfo(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class QueryResponse(BaseModel):
    query_id: str
    answer: str
    sources: list[SourceResponse]
    usage: UsageInfo
    latency_ms: int
    cache_hit: bool = False
```

## 3. RAGService (`app/application/services/rag_service.py`)

```python
class RagService:
    def __init__(self, session, kb_service, retrieval, prompt_builder, llm):
        ...

    async def query(self, user_id: UUID, cmd: QueryRequest) -> QueryResponse:
        t0 = time.monotonic()

        # 1. 权限检查
        kb = await self.kb_service.assert_owner(cmd.knowledge_base_id, user_id)

        # 2. 检索
        chunks = await self.retrieval.retrieve(
            collection=kb.vector_collection,
            query=cmd.question,
            top_k=cmd.top_k,
        )

        # 3. 空结果处理
        if not chunks:
            return QueryResponse(
                query_id=str(uuid4()),
                answer="当前知识库没有可用资料。",
                sources=[],
                usage=UsageInfo(0, 0, 0),
                latency_ms=int((time.monotonic() - t0) * 1000),
            )

        # 4. 构建 Prompt
        messages = self.prompt_builder.build(cmd.question, chunks)

        # 5. LLM 生成
        result = await self.llm.generate(messages, temperature=cmd.temperature)

        # 6. 持久化
        query_id = await self._persist(
            user_id, kb.id, cmd.question, result, chunks,
            latency=int((time.monotonic() - t0) * 1000),
        )

        return QueryResponse(...)
```

## 4. RetrievalService (`app/application/services/retrieval_service.py`)

```python
class RetrievalService:
    def __init__(self, embedder: BgeEmbeddingProvider, vector_store: VectorStore):
        ...

    async def retrieve(
        self, collection: str, query: str, top_k: int = 5
    ) -> list[RetrievedChunk]:
        # 1. 生成 query embedding
        vector = await self.embedder.embed_query(query)

        # 2. 检索 top_k * 3
        points = await self.vector_store.query(collection, vector, top_k * 3)

        # 3. 过滤低分
        filtered = [p for p in points if p.payload.get("score", 0) > 0]

        # 4. 返回 top_k
        return [self._to_chunk(p, i) for i, p in enumerate(filtered[:top_k])]
```

## 5. PromptBuilder (`app/application/services/prompt_builder.py`)

```python
SYSTEM_PROMPT = """你是一个严谨的知识库问答助手。
请只根据给定的上下文回答问题。
如果上下文不足以回答，请明确说明"根据当前知识库资料无法确定"。
回答时尽量简洁，并在关键结论后标注来源编号，例如 [1]、[2]。"""

def build_messages(question: str, chunks: list[RetrievedChunk]) -> list[dict]:
    context_blocks = []
    for i, c in enumerate(chunks):
        context_blocks.append(
            f"[{i + 1}] 文件：{c.filename}，页码：{c.page_number or '-'}\n{c.content}"
        )
    context = "\n\n".join(context_blocks)

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"问题：{question}\n\n上下文：\n{context}\n\n回答："},
    ]
```

## 6. LLM Provider

### 6.1 协议 (`app/infrastructure/providers/llm/base.py`)

```python
@dataclass
class GenerationResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class LLMProvider(Protocol):
    async def generate(
        self, messages: list[dict], temperature: float = 0.2
    ) -> GenerationResult: ...
```

### 6.2 MiMo 实现

```python
class MimoLlmProvider:
    def __init__(self, base_url: str, model: str, api_key: str, timeout: int = 60):
        ...

    async def generate(self, messages, temperature=0.2) -> GenerationResult:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 1024,
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            data = resp.json()
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return GenerationResult(
                text=choice["message"]["content"],
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )
```

## 7. 查询路由 (`app/api/v1/routes/queries.py`)

```python
@router.post("/queries", response_model=ApiResponse[QueryResponse])
async def create_query(
    body: QueryRequest,
    request: Request,
    user: User | None = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    rag_service = _build_rag_service(session)
    user_id = user.id if user else uuid4()
    result = await rag_service.query(user_id, body)
    return ApiResponse(data=result, request_id=...)
```

## 8. 文件落点汇总

```
[改] app/application/services/rag_service.py
[新] app/application/services/retrieval_service.py
[新] app/application/services/prompt_builder.py
[新] app/schemas/query.py
[新] app/infrastructure/providers/llm/base.py
[改] app/infrastructure/providers/llm/mimo_provider.py
[新] app/api/v1/routes/queries.py
[改] app/api/v1/__init__.py
```
