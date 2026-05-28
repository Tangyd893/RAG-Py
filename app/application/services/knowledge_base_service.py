"""知识库应用服务——用例编排与事务边界。"""

import hashlib
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.errors import ResourceNotFoundError, ValidationFailedError
from app.infrastructure.db.models import DocumentStatus, KnowledgeBase, KBStatus
from app.infrastructure.db.repository import (
    KnowledgeBaseRepository,
)
from app.schemas.common import PaginatedData, PaginationParams
from app.schemas.knowledge_base import CreateKBRequest, KBDetailResponse, KBResponse


class KnowledgeBaseService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = KnowledgeBaseRepository(session)

    async def create(self, owner_id: uuid.UUID, cmd: CreateKBRequest) -> KnowledgeBase:
        if cmd.chunk_overlap >= cmd.chunk_size / 2:
            raise ValidationFailedError("chunk_overlap 必须小于 chunk_size/2")

        kb_id = uuid.uuid4()
        collection = self._build_collection(kb_id)

        kb = KnowledgeBase(
            id=kb_id,
            owner_id=owner_id,
            name=cmd.name,
            description=cmd.description,
            embedding_model="bge-m3",
            vector_collection=collection,
            chunk_size=cmd.chunk_size,
            chunk_overlap=cmd.chunk_overlap,
            retrieval_top_k=cmd.retrieval_top_k,
            status=KBStatus.active,
        )
        self.session.add(kb)
        await self.session.flush()

        try:
            from app.core.config import settings
            from app.infrastructure.vector_store.chroma_store import ChromaVectorStore
            from app.infrastructure.providers.embedding.bge_provider import (
                BgeEmbeddingProvider,
            )

            embedder = BgeEmbeddingProvider()
            vector_store = ChromaVectorStore(settings.chroma_host, settings.chroma_port)
            await vector_store.ensure_collection(collection, embedder.dimensions)
        except Exception:
            pass

        return kb

    async def list_by_user(
        self, owner_id: uuid.UUID, pagination: PaginationParams
    ) -> PaginatedData[KBResponse]:
        offset = (pagination.page - 1) * pagination.page_size
        kbs, total = await self.repo.list_by_owner(
            owner_id, offset=offset, limit=pagination.page_size
        )
        return PaginatedData[KBResponse](
            items=[self._to_response(kb) for kb in kbs],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def get_detail(self, kb_id: uuid.UUID, owner_id: uuid.UUID) -> KBDetailResponse:
        kb = await self.repo.get(kb_id)
        if not kb or kb.owner_id != owner_id:
            raise ResourceNotFoundError(
                entity="KnowledgeBase", entity_id=str(kb_id)
            )

        stats = await self._document_stats(kb_id)
        return KBDetailResponse(
            id=str(kb.id),
            name=kb.name,
            description=kb.description,
            embedding_model=kb.embedding_model,
            vector_collection=kb.vector_collection,
            chunk_size=kb.chunk_size,
            chunk_overlap=kb.chunk_overlap,
            retrieval_top_k=kb.retrieval_top_k,
            status=kb.status.value,
            created_at=kb.created_at.isoformat() if kb.created_at else "",
            updated_at=kb.updated_at.isoformat() if kb.updated_at else "",
            document_count=stats.get("total", 0),
            indexed_count=stats.get("indexed", 0),
            failed_count=stats.get("failed", 0),
        )

    async def assert_owner(self, kb_id: uuid.UUID, owner_id: uuid.UUID) -> KnowledgeBase:
        kb = await self.repo.get(kb_id)
        if not kb or kb.owner_id != owner_id:
            raise ResourceNotFoundError(
                entity="KnowledgeBase", entity_id=str(kb_id)
            )
        return kb

    @staticmethod
    def _build_collection(kb_id: uuid.UUID) -> str:
        model_hash = hashlib.md5(b"bge-m3").hexdigest()[:8]
        return f"kb_{kb_id.hex}_{model_hash}"

    @staticmethod
    def _to_response(kb: KnowledgeBase) -> KBResponse:
        return KBResponse(
            id=str(kb.id),
            name=kb.name,
            description=kb.description,
            embedding_model=kb.embedding_model,
            vector_collection=kb.vector_collection,
            chunk_size=kb.chunk_size,
            chunk_overlap=kb.chunk_overlap,
            retrieval_top_k=kb.retrieval_top_k,
            status=kb.status.value,
            created_at=kb.created_at.isoformat() if kb.created_at else "",
            updated_at=kb.updated_at.isoformat() if kb.updated_at else "",
        )

    async def _document_stats(self, kb_id: uuid.UUID) -> dict[str, int]:
        from sqlalchemy import func, select

        from app.infrastructure.db.models import Document

        q = (
            select(
                func.count().label("total"),
                func.count().filter(Document.status == DocumentStatus.indexed).label("indexed"),
                func.count().filter(Document.status == DocumentStatus.failed).label("failed"),
            )
            .where(Document.knowledge_base_id == kb_id)
        )
        result = await self.session.execute(q)
        row = result.one()
        return {
            "total": row.total,
            "indexed": row.indexed,
            "failed": row.failed,
        }
