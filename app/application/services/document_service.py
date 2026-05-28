"""文档应用服务——上传、去重、状态查询。"""

import hashlib
import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.errors import (
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationFailedError,
)
from app.infrastructure.db.models import Document, DocumentStatus
from app.infrastructure.db.repository import DocumentRepository
from app.infrastructure.storage.base import ObjectStorage
from app.schemas.document import DocumentResponse, DocumentUploadResponse

ALLOWED_TYPES = {
    "text/plain",
    "text/markdown",
    "text/x-markdown",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class DocumentService:
    def __init__(self, session: AsyncSession, storage: ObjectStorage):
        self.session = session
        self.storage = storage
        self.repo = DocumentRepository(session)

    async def upload(
        self, kb_id: uuid.UUID, user_id: uuid.UUID, file: UploadFile
    ) -> DocumentUploadResponse:
        if file.content_type and file.content_type not in ALLOWED_TYPES:
            raise ValidationFailedError(
                f"不支持的文件类型: {file.content_type}"
            )

        if file.size and file.size > MAX_FILE_SIZE:
            raise ValidationFailedError("文件大小超过 50MB 限制")

        content = await file.read()
        if not content:
            raise ValidationFailedError("上传文件为空")

        checksum = self._compute_checksum(content)

        duplicate = await self._check_duplicate(kb_id, checksum)
        if duplicate:
            if duplicate.status == DocumentStatus.indexed:
                return DocumentUploadResponse(
                    document_id=str(duplicate.id),
                    status=duplicate.status.value,
                    duplicate=True,
                )
            if duplicate.status == DocumentStatus.failed:
                pass
            else:
                return DocumentUploadResponse(
                    document_id=str(duplicate.id),
                    status=duplicate.status.value,
                    duplicate=True,
                )

        object_key = f"{uuid.uuid4().hex}.bin"
        await self.storage.put(object_key, content)

        doc = Document(
            id=uuid.uuid4(),
            knowledge_base_id=kb_id,
            uploader_id=user_id,
            filename=file.filename or "unknown",
            content_type=file.content_type or "application/octet-stream",
            object_key=object_key,
            file_size=len(content),
            checksum=checksum,
            status=DocumentStatus.uploaded,
        )
        self.session.add(doc)
        await self.session.flush()

        return DocumentUploadResponse(
            document_id=str(doc.id),
            status=doc.status.value,
            duplicate=False,
        )

    async def get_by_id(self, document_id: uuid.UUID) -> DocumentResponse:
        doc = await self.repo.get(document_id)
        if not doc:
            raise ResourceNotFoundError(
                entity="Document", entity_id=str(document_id)
            )
        return self._to_response(doc)

    async def _check_duplicate(
        self, kb_id: uuid.UUID, checksum: str
    ) -> Document | None:
        return await self.repo.get_by_kb_and_checksum(kb_id, checksum)

    @staticmethod
    def _compute_checksum(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def _to_response(doc: Document) -> DocumentResponse:
        return DocumentResponse(
            id=str(doc.id),
            knowledge_base_id=str(doc.knowledge_base_id),
            filename=doc.filename,
            content_type=doc.content_type,
            file_size=doc.file_size,
            checksum=doc.checksum,
            status=doc.status.value,
            error_message=doc.error_message,
            created_at=doc.created_at.isoformat() if doc.created_at else "",
            updated_at=doc.updated_at.isoformat() if doc.updated_at else "",
        )
