"""文档 API 路由。"""

import uuid

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.application.services.document_service import DocumentService
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_session
from app.infrastructure.storage.local_storage import LocalStorage
from app.core.config import settings
from app.schemas.common import ApiResponse
from app.schemas.document import DocumentResponse, DocumentUploadResponse

router = APIRouter(tags=["documents"])


def _get_storage() -> LocalStorage:
    return LocalStorage(settings.local_storage_path)


@router.post(
    "/knowledge-bases/{kb_id}/documents",
    response_model=ApiResponse[DocumentUploadResponse],
)
async def upload_document(
    kb_id: uuid.UUID,
    request: Request,
    file: UploadFile = File(...),
    user: User | None = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not file.filename:
        from app.domain.errors import ValidationFailedError
        raise ValidationFailedError("文件名为空")

    storage = _get_storage()
    service = DocumentService(session, storage)
    user_id = user.id if user else uuid.uuid4()
    result = await service.upload(kb_id, user_id, file)
    return ApiResponse(
        data=result,
        request_id=getattr(request.state, "request_id", ""),
    )


@router.get(
    "/documents/{document_id}",
    response_model=ApiResponse[DocumentResponse],
)
async def get_document(
    document_id: uuid.UUID,
    request: Request,
    user: User | None = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    storage = _get_storage()
    service = DocumentService(session, storage)
    result = await service.get_by_id(document_id)
    return ApiResponse(
        data=result,
        request_id=getattr(request.state, "request_id", ""),
    )
