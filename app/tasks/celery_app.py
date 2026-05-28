"""Celery 应用配置。"""

from celery import Celery

from app.core.config import settings

celery_app = Celery("rag_py")

celery_app.conf.update(
    broker_url=settings.celery_broker_url,
    result_backend=settings.celery_result_backend,
    task_default_queue="indexing",
)
