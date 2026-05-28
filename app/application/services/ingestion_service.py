"""文档索引流水线编排——解析 → 分块 → 向量化 → 持久化。"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.errors import ResourceNotFoundError
from app.infrastructure.db.models import (
    Chunk,
    Document,
    DocumentStatus,
    IndexingJob,
    JobStatus,
    KnowledgeBase,
)
from app.infrastructure.parsing.base import DocumentParser
from app.infrastructure.parsing.md_parser import MdParser
from app.infrastructure.parsing.txt_parser import TxtParser
from app.infrastructure.providers.embedding.bge_provider import BgeEmbeddingProvider
from app.infrastructure.storage.base import ObjectStorage
from app.infrastructure.text_splitter.splitter import ChunkDraft, TextSplitter
from app.infrastructure.vector_store.base import VectorPoint, VectorStore


class IngestionService:
    """文档索引流水线编排器——分阶段执行，每阶段更新状态和进度。"""

    def __init__(
        self,
        session: AsyncSession,
        storage: ObjectStorage,
        vector_store: VectorStore,
        embedder: BgeEmbeddingProvider | None = None,
    ):
        self.session = session
        self.storage = storage
        self.vector_store = vector_store
        self.embedder = embedder or BgeEmbeddingProvider()

    async def index(self, document_id: uuid.UUID, task_id: str) -> None:
        doc = await self.session.get(Document, document_id)
        if not doc:
            raise ResourceNotFoundError(entity="Document", entity_id=str(document_id))

        kb = await self.session.get(KnowledgeBase, doc.knowledge_base_id)
        if not kb:
            raise ResourceNotFoundError(
                entity="KnowledgeBase", entity_id=str(doc.knowledge_base_id)
            )

        job = await self._ensure_job(document_id, task_id)

        try:
            await self._cleanup_previous(document_id, kb.vector_collection)

            text = await self._phase_parse(doc)
            self._update_progress(job, 40)
            await self._flush()

            drafts = self._phase_chunk(doc, text, kb)
            self._update_progress(job, 55)
            await self._flush()

            vectors = await self._phase_embed(doc, drafts, kb)
            self._update_progress(job, 80)
            await self._flush()

            await self._phase_persist(doc, kb, drafts, vectors)
            self._update_progress(job, 95)
            await self._flush()

            await self._phase_finalize(doc, job)
        except Exception as exc:
            await self._mark_failed(doc, job, str(exc))
            raise

    async def _ensure_job(
        self, document_id: uuid.UUID, task_id: str
    ) -> IndexingJob:
        result = await self.session.execute(
            select(IndexingJob).where(
                IndexingJob.document_id == document_id,
                IndexingJob.status.in_([JobStatus.queued, JobStatus.running]),
            ).limit(1)
        )
        job = result.scalar_one_or_none()
        if job:
            job.status = JobStatus.running
            job.task_id = task_id
            job.attempt += 1
            job.started_at = datetime.now(timezone.utc)
        else:
            job = IndexingJob(
                id=uuid.uuid4(),
                document_id=document_id,
                task_id=task_id,
                status=JobStatus.running,
                attempt=1,
                started_at=datetime.now(timezone.utc),
            )
            self.session.add(job)
        return job

    async def _cleanup_previous(
        self, document_id: uuid.UUID, collection_name: str
    ) -> None:
        await self.session.execute(
            delete(Chunk).where(Chunk.document_id == document_id)
        )
        try:
            await self.vector_store.delete_by_document(
                collection_name, str(document_id)
            )
        except Exception:
            pass

    async def _phase_parse(self, doc: Document) -> str:
        doc.status = DocumentStatus.parsing

        parser = self._get_parser(doc.content_type)
        content = await self.storage.get(doc.object_key)
        if content is None:
            raise ResourceNotFoundError(
                entity="File", entity_id=doc.object_key
            )
        return await parser.parse(content, doc.filename)

    async def _phase_chunk(
        self, doc: Document, text: str, kb: KnowledgeBase
    ) -> list[ChunkDraft]:
        doc.status = DocumentStatus.chunking
        splitter = TextSplitter(
            chunk_size=kb.chunk_size, chunk_overlap=kb.chunk_overlap
        )
        return splitter.split(text)

    async def _phase_embed(
        self, doc: Document, drafts: list[ChunkDraft], kb: KnowledgeBase
    ) -> list[list[float]]:
        doc.status = DocumentStatus.embedding
        texts = [d.content for d in drafts]
        return await self.embedder.embed_texts(texts)

    async def _phase_persist(
        self,
        doc: Document,
        kb: KnowledgeBase,
        drafts: list[ChunkDraft],
        vectors: list[list[float]],
    ) -> None:
        chunks: list[Chunk] = []
        points: list[VectorPoint] = []

        for i, (draft, vector) in enumerate(zip(drafts, vectors)):
            chunk_id = uuid.uuid4()
            chunk = Chunk(
                id=chunk_id,
                document_id=doc.id,
                knowledge_base_id=kb.id,
                chunk_index=draft.chunk_index,
                content=draft.content,
                content_hash=self._hash_text(draft.content),
                token_count=draft.token_count,
                page_number=draft.page_number,
                start_offset=draft.start_offset,
                end_offset=draft.end_offset,
                metadata_=draft.metadata,
                vector_id=f"chunk_{chunk_id.hex}",
            )
            chunks.append(chunk)

            points.append(
                VectorPoint(
                    id=chunk.vector_id,
                    vector=vector,
                    payload={
                        "knowledge_base_id": str(kb.id),
                        "document_id": str(doc.id),
                        "chunk_id": str(chunk_id),
                        "chunk_index": draft.chunk_index,
                        "content": draft.content[:500],
                        "filename": doc.filename,
                        "page_number": draft.page_number or 0,
                    },
                )
            )

        for chunk in chunks:
            self.session.add(chunk)
        await self.session.flush()

        await self.vector_store.upsert(kb.vector_collection, points)

    async def _phase_finalize(self, doc: Document, job: IndexingJob) -> None:
        doc.status = DocumentStatus.indexed
        doc.error_message = None
        job.status = JobStatus.succeeded
        job.finished_at = datetime.now(timezone.utc)
        job.progress = 100

    async def _mark_failed(
        self, doc: Document, job: IndexingJob, error: str
    ) -> None:
        doc.status = DocumentStatus.failed
        doc.error_message = error[:1000]
        job.status = JobStatus.failed
        job.error_message = error[:1000]
        job.finished_at = datetime.now(timezone.utc)
        await self._flush()

    async def _flush(self) -> None:
        await self.session.flush()

    @staticmethod
    def _get_parser(content_type: str) -> DocumentParser:
        if content_type in ("text/plain",):
            return TxtParser()
        if content_type in ("text/markdown", "text/x-markdown"):
            return MdParser()
        return TxtParser()

    @staticmethod
    def _update_progress(job: IndexingJob, progress: int) -> None:
        job.progress = progress

    @staticmethod
    def _hash_text(text: str) -> str:
        import hashlib

        return hashlib.sha256(text.encode("utf-8")).hexdigest()
