import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import domain_error_handler, http_exception_handler
from app.api.v1 import api_v1_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.domain.errors import DomainError

setup_logging(settings.log_level)

app = FastAPI(title="RAG-Py API", version="0.1.0")
app.include_router(api_v1_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


app.add_exception_handler(DomainError, domain_error_handler)
app.add_exception_handler(Exception, http_exception_handler)
