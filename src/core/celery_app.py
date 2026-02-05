import os
from celery import Celery

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL"))

celery_app = Celery("cinema_tasks", broker=CELERY_BROKER_URL, backend=CELERY_BROKER_URL)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup_tokens_daily": {
        "task": "src.tasks.auth.delete_expired_tokens",
        "schedule": float(os.getenv("TOKEN_CLEANUP_INTERVAL", 86400.0)),
    },
}

# Auto-discovery of tasks in src/tasks
celery_app.autodiscover_tasks(["src"])
