"""RAG 查询 API 路由。"""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.application.services.knowledge_base_service import KnowledgeBaseService
from app.application.services.rag_service import RagService
from app.application.services.retrieval_service import RetrievalService
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_session
from app.infrastructure.providers.embedding.bge_provider import BgeEmbeddingProvider
from app.infrastructure.providers.llm.mimo_provider import MimoLlmProvider
from app.infrastructure.vector_store.chroma_store import ChromaVectorStore
from app.core.config import settings
from app.schemas.common import ApiResponse
from app.schemas.query import QueryRequest, QueryResponse

router = APIRouter(prefix="/queries", tags=["queries"])


def _build_rag_service(session: AsyncSession) -> RagService:
    kb_service = KnowledgeBaseService(session)
    embedder = BgeEmbeddingProvider()
    vector_store = ChromaVectorStore(settings.chroma_host, settings.chroma_port)
    retrieval = RetrievalService(embedder, vector_store)
    llm = MimoLlmProvider()
    return RagService(session, kb_service, retrieval, llm)


@router.post("", response_model=ApiResponse[QueryResponse])
async def create_query(
    body: QueryRequest,
    request: Request,
    user: User | None = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    rag_service = _build_rag_service(session)
    user_id = user.id if user else uuid.uuid4()
    result = await rag_service.query(user_id, body)
    return ApiResponse(
        data=result,
        request_id=getattr(request.state, "request_id", ""),
    )
