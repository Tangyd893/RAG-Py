"""混合检索服务——Dense + Sparse 检索 + RRF 融合。"""

import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.retrieval_service import RetrievedChunk, RetrievalService
from app.infrastructure.db.models import Chunk
from app.infrastructure.retrieval.bm25 import BM25Index, bm25_cache
from app.infrastructure.vector_store.base import VectorStore


_RRF_K = 60


class HybridRetrievalService:
    """混合检索——向量检索 + BM25 稀疏检索 → RRF 融合。"""

    def __init__(
        self,
        session: AsyncSession,
        dense_service: RetrievalService,
        vector_store: VectorStore,
    ):
        self._session = session
        self._dense = dense_service
        self._vector_store = vector_store

    async def retrieve(
        self,
        collection: str,
        kb_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        candidates = top_k * 2

        # Dense 检索
        dense_chunks = await self._dense.retrieve(collection, query, candidates)

        # Sparse (BM25) 检索
        sparse_chunks = await self._sparse_retrieve(kb_id, query, candidates)

        if not dense_chunks and not sparse_chunks:
            return []

        if not sparse_chunks:
            return dense_chunks[:top_k]
        if not dense_chunks:
            return sparse_chunks[:top_k]

        # RRF 融合
        fused = self._rrf_fuse(dense_chunks, sparse_chunks, top_k)
        return fused

    async def _sparse_retrieve(
        self, kb_id: str, query: str, top_k: int
    ) -> list[RetrievedChunk]:
        index = bm25_cache.get(kb_id)
        if index is None:
            index = await self._build_bm25_index(kb_id)
            if index is None:
                return []
            bm25_cache.set(kb_id, index)

        results = index.search(query, top_k)
        chunks: list[RetrievedChunk] = []
        for meta, score in results:
            chunks.append(
                RetrievedChunk(
                    chunk_id=meta.get("chunk_id", ""),
                    document_id=meta.get("document_id", ""),
                    filename=meta.get("filename", ""),
                    content=meta.get("content", ""),
                    score=score,
                    rank=0,
                    metadata=meta,
                )
            )
        return chunks

    async def _build_bm25_index(self, kb_id: str) -> BM25Index | None:
        kb_uuid = uuid.UUID(kb_id)
        result = await self._session.execute(
            select(Chunk).where(Chunk.knowledge_base_id == kb_uuid)
        )
        rows = result.scalars().all()
        if not rows:
            return None

        corpus: list[tuple[str, dict]] = [
            (
                row.content,
                {
                    "chunk_id": str(row.id),
                    "document_id": str(row.document_id),
                    "content": row.content,
                    "chunk_index": row.chunk_index,
                },
            )
            for row in rows
        ]
        return BM25Index(corpus)

    @staticmethod
    def _rrf_fuse(
        dense: list[RetrievedChunk],
        sparse: list[RetrievedChunk],
        top_k: int,
    ) -> list[RetrievedChunk]:
        """Reciprocal Rank Fusion——融合两路排序结果。"""
        scores: dict[str, tuple[RetrievedChunk, float]] = {}
        for rank, chunk in enumerate(dense):
            cid = chunk.chunk_id
            scores[cid] = (chunk, 1.0 / (_RRF_K + rank + 1))
        for rank, chunk in enumerate(sparse):
            cid = chunk.chunk_id
            rrf_score = 1.0 / (_RRF_K + rank + 1)
            if cid in scores:
                _, prev = scores[cid]
                scores[cid] = (chunk, prev + rrf_score)
            else:
                scores[cid] = (chunk, rrf_score)

        sorted_items = sorted(scores.values(), key=lambda x: x[1], reverse=True)
        result: list[RetrievedChunk] = []
        for i, (chunk, rrf_score) in enumerate(sorted_items[:top_k]):
            chunk.rank = i + 1
            chunk.score = rrf_score
            result.append(chunk)
        return result
