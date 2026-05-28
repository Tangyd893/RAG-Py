"""统一 API 响应模型。"""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

TData = TypeVar("TData")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class ApiResponse(BaseModel, Generic[TData]):
    data: Optional[TData] = None
    error: Optional[ErrorDetail] = None
    request_id: str


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20


class PaginatedData(BaseModel, Generic[TData]):
    items: list[TData]
    total: int
    page: int
    page_size: int
