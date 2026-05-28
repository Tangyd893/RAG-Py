from fastapi import APIRouter

from .routes.health import router as health_router
from .routes.knowledge_bases import router as kb_router
from .routes.documents import router as documents_router
from .routes.queries import router as queries_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(kb_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(queries_router)
