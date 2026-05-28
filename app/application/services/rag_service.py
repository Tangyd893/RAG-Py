"""RAG 查询编排服务——检索 → Prompt → LLM → 持久化。"""

import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.knowledge_base_service import KnowledgeBaseService
from app.application.services.prompt_builder import build_messages
from app.application.services.retrieval_service import RetrievalService
from app.domain.errors import ResourceNotFoundError
from app.infrastructure.db.models import QueryLog, QuerySource, QueryStatusEnum
from app.infrastructure.providers.llm.base import LLMProvider
from app.infrastructure.vector_store.base import VectorStore
from app.schemas.query import QueryRequest, QueryResponse, SourceResponse, UsageInfo


class RagService:
    """RAG 查询主编排器——检索上下文 + LLM 生成 + 记录持久化。"""

    def __init__(
        self,
        session: AsyncSession,
        kb_service: KnowledgeBaseService,
        retrieval: RetrievalService,
        llm: LLMProvider,
    ):
        self.session = session
        self.kb_service = kb_service
        self.retrieval = retrieval
        self.llm = llm

    async def query(
        self, user_id: uuid.UUID, cmd: QueryRequest
    ) -> QueryResponse:
        t0 = time.monotonic()
        kb_id = uuid.UUID(cmd.knowledge_base_id)

        kb = await self.kb_service.repo.get(kb_id)
        if not kb or kb.owner_id != user_id:
            raise ResourceNotFoundError(
                entity="KnowledgeBase", entity_id=str(kb_id)
            )

        chunks = await self.retrieval.retrieve(
            collection=kb.vector_collection,
            query=cmd.question,
            top_k=cmd.top_k,
        )

        if not chunks:
            query_id = uuid.uuid4()
            return QueryResponse(
                query_id=str(query_id),
                answer="当前知识库没有可用资料。",
                sources=[],
                usage=UsageInfo(),
                latency_ms=int((time.monotonic() - t0) * 1000),
            )

        messages = build_messages(cmd.question, chunks)

        result = await self.llm.generate(messages, temperature=cmd.temperature)

        latency_ms = int((time.monotonic() - t0) * 1000)
        query_id = uuid.uuid4()

        await self._persist(
            query_id=query_id,
            user_id=user_id,
            kb_id=kb_id,
            question=cmd.question,
            answer=result.text,
            usage=result,
            chunks=chunks,
            latency_ms=latency_ms,
        )

        sources = self._build_sources(query_id, chunks)

        return QueryResponse(
            query_id=str(query_id),
            answer=result.text,
            sources=sources,
            usage=UsageInfo(
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                total_tokens=result.total_tokens,
            ),
            latency_ms=latency_ms,
        )

    async def _persist(
        self,
        query_id: uuid.UUID,
        user_id: uuid.UUID,
        kb_id: uuid.UUID,
        question: str,
        answer: str,
        usage,
        chunks,
        latency_ms: int,
    ) -> None:
        log = QueryLog(
            id=query_id,
            user_id=user_id,
            knowledge_base_id=kb_id,
            question=question,
            answer=answer,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            latency_ms=latency_ms,
            model_name=getattr(self.llm, "model", ""),
            status=QueryStatusEnum.succeeded,
        )
        self.session.add(log)

        for i, chunk in enumerate(chunks):
            source_id = uuid.uuid4()
            source = QuerySource(
                id=source_id,
                query_log_id=query_id,
                chunk_id=uuid.UUID(chunk.chunk_id) if chunk.chunk_id else None,
                document_id=uuid.UUID(chunk.document_id) if chunk.document_id else None,
                rank=i + 1,
                score=chunk.score,
                content=chunk.content[:2000],
                metadata_=(chunk.metadata or {}),
            )
            self.session.add(source)

        await self.session.flush()

    @staticmethod
    def _build_sources(query_id, chunks) -> list[SourceResponse]:
        return [
            SourceResponse(
                source_id=f"src_{i + 1}",
                document_id=c.document_id,
                chunk_id=c.chunk_id,
                filename=c.filename,
                page_number=c.page_number,
                score=c.score,
                content=c.content[:500],
            )
            for i, c in enumerate(chunks)
        ]
