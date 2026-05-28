from celery import Celery

celery_app = Celery("rag_py")

celery_app.conf.update(
    broker_url="redis://redis:6379/1",
    result_backend="redis://redis:6379/2",
    task_default_queue="indexing",
)
