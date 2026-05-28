"""文档请求/响应 Schema。"""

from typing import Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    knowledge_base_id: str
    filename: str
    content_type: str
    file_size: int
    checksum: str
    status: str
    error_message: Optional[str]
    created_at: str
    updated_at: str


class DocumentUploadResponse(BaseModel):
    document_id: str
    status: str
    duplicate: bool = False
