from core import celery_app


@celery_app.task(name="src.tasks.auth.delete_expired_tokens")
def delete_expired_tokens():
    pass
