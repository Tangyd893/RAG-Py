"""知识库请求/响应 Schema。"""

from typing import Optional

from pydantic import BaseModel, field_validator


class CreateKBRequest(BaseModel):
    name: str
    description: Optional[str] = None
    chunk_size: int = 500
    chunk_overlap: int = 50
    retrieval_top_k: int = 5

    @field_validator("chunk_size")
    @classmethod
    def chunk_size_range(cls, v: int) -> int:
        if not 200 <= v <= 1500:
            raise ValueError("chunk_size 必须在 200-1500 之间")
        return v

    @field_validator("chunk_overlap")
    @classmethod
    def chunk_overlap_limit(cls, v: int) -> int:
        if v < 0:
            raise ValueError("chunk_overlap 不能为负数")
        return v


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
