"""全局异常处理器——将领域异常映射为统一 HTTP 响应。"""

import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

from app.domain.errors import (
    DomainError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationFailedError,
)
from app.schemas.common import ApiResponse, ErrorDetail


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    request_id = _get_request_id(request)
    status_code = _map_status_code(exc)
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse[None](
            data=None,
            error=ErrorDetail(code=exc.code, message=str(exc)),
            request_id=request_id,
        ).model_dump(),
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    from fastapi.exceptions import HTTPException as FastAPIHTTPException

    if isinstance(exc, FastAPIHTTPException):
        request_id = _get_request_id(request)
        return JSONResponse(
            status_code=exc.status_code,
            content=ApiResponse[None](
                data=None,
                error=ErrorDetail(
                    code="HTTP_ERROR",
                    message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
                ),
                request_id=request_id,
            ).model_dump(),
        )
    return await _unhandled_handler(request, exc)


async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = _get_request_id(request)
    return JSONResponse(
        status_code=500,
        content=ApiResponse[None](
            data=None,
            error=ErrorDetail(code="INTERNAL_ERROR", message="Internal server error"),
            request_id=request_id,
        ).model_dump(),
    )


def _map_status_code(exc: DomainError) -> int:
    if isinstance(exc, ResourceNotFoundError):
        return 404
    if isinstance(exc, ValidationFailedError):
        return 422
    if isinstance(exc, ResourceConflictError):
        return 409
    return 400


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", f"req_{uuid.uuid4().hex[:12]}")
