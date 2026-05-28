"""向量检索服务——Query Embedding → Chroma 检索 → 结果过滤。"""

from dataclasses import dataclass
from typing import Any

from app.infrastructure.providers.embedding.bge_provider import BgeEmbeddingProvider
from app.infrastructure.vector_store.base import VectorStore


@dataclass
class RetrievedChunk:
    """检索结果片段。"""
    chunk_id: str
    document_id: str
    filename: str
    content: str
    score: float
    rank: int
    page_number: int | None = None
    metadata: dict[str, Any] | None = None


class RetrievalService:
    """向量检索服务——生成 query embedding 并检索 Chroma。"""

    def __init__(
        self,
        embedder: BgeEmbeddingProvider,
        vector_store: VectorStore,
    ):
        self.embedder = embedder
        self.vector_store = vector_store

    async def retrieve(
        self, collection: str, query: str, top_k: int = 5
    ) -> list[RetrievedChunk]:
        vector = await self.embedder.embed_query(query)

        points = await self.vector_store.query(collection, vector, top_k * 3)

        chunks: list[RetrievedChunk] = []
        for i, point in enumerate(points):
            payload = point.payload or {}
            chunks.append(
                RetrievedChunk(
                    chunk_id=payload.get("chunk_id", point.id),
                    document_id=payload.get("document_id", ""),
                    filename=payload.get("filename", ""),
                    content=payload.get("content", ""),
                    score=payload.get("score", 0.0),
                    rank=i + 1,
                    page_number=payload.get("page_number"),
                    metadata=payload,
                )
            )

        return chunks[:top_k]
