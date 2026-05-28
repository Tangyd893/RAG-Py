"""知识库 API 路由。"""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_pagination
from app.application.services.knowledge_base_service import KnowledgeBaseService
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_session
from app.schemas.common import ApiResponse, PaginationParams
from app.schemas.knowledge_base import CreateKBRequest, KBDetailResponse, KBResponse
from app.schemas.common import PaginatedData

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.post("", response_model=ApiResponse[KBResponse])
async def create_knowledge_base(
    body: CreateKBRequest,
    request: Request,
    user: User | None = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = KnowledgeBaseService(session)
    owner_id = user.id if user else uuid.uuid4()
    kb = await service.create(owner_id, body)
    return ApiResponse(
        data=KBResponse(
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
        ),
        request_id=getattr(request.state, "request_id", ""),
    )


@router.get("", response_model=ApiResponse[PaginatedData[KBResponse]])
async def list_knowledge_bases(
    request: Request,
    user: User | None = Depends(get_current_user),
    pagination: PaginationParams = Depends(get_pagination),
    session: AsyncSession = Depends(get_session),
):
    service = KnowledgeBaseService(session)
    owner_id = user.id if user else uuid.uuid4()
    result = await service.list_by_user(owner_id, pagination)
    return ApiResponse(
        data=result,
        request_id=getattr(request.state, "request_id", ""),
    )


@router.get("/{kb_id}", response_model=ApiResponse[KBDetailResponse])
async def get_knowledge_base(
    kb_id: uuid.UUID,
    request: Request,
    user: User | None = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = KnowledgeBaseService(session)
    owner_id = user.id if user else uuid.uuid4()
    detail = await service.get_detail(kb_id, owner_id)
    return ApiResponse(
        data=detail,
        request_id=getattr(request.state, "request_id", ""),
    )
