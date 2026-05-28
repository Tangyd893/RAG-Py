from fastapi import FastAPI

from app.api.v1 import api_v1_router
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging(settings.log_level)

app = FastAPI(title="RAG-Py API", version="0.1.0")
app.include_router(api_v1_router)
