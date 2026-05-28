"""Celery 索引任务——异步文档索引入口。"""

import asyncio
import uuid

from app.tasks.celery_app import celery_app


@celery_app.task(
    name="index_document",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    default_retry_delay=10,
)
def index_document(self, document_id: str) -> None:
    """异步索引文档：解析 → 分块 → 向量化 → 入库。"""

    async def _run():
        from sqlalchemy.ext.asyncio import AsyncSession

        from app.application.services.ingestion_service import IngestionService
        from app.core.config import settings
        from app.infrastructure.db.session import async_session
        from app.infrastructure.providers.embedding.bge_provider import (
            BgeEmbeddingProvider,
        )
        from app.infrastructure.storage.local_storage import LocalStorage
        from app.infrastructure.vector_store.chroma_store import ChromaVectorStore

        storage = LocalStorage(settings.local_storage_path)
        vector_store = ChromaVectorStore(settings.chroma_host, settings.chroma_port)
        embedder = BgeEmbeddingProvider()

        async with async_session() as session:
            service = IngestionService(session, storage, vector_store, embedder)
            await service.index(uuid.UUID(document_id), task_id=self.request.id)

    asyncio.run(_run())
