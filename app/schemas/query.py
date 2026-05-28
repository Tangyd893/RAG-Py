"""RAG 查询请求与响应 Schema。"""

from typing import Optional

from pydantic import BaseModel


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
    page_number: Optional[int] = None
    score: float
    content: str


class UsageInfo(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class QueryResponse(BaseModel):
    query_id: str
    answer: str
    sources: list[SourceResponse]
    usage: UsageInfo
    latency_ms: int = 0
    cache_hit: bool = False
