from src.core.celery_app import celery_app
from src.notifications.email import send_email as sync_send_email


@celery_app.task(
    name="src.tasks.email.send_email_task",
    # If SendGrid returns an error or the network fails, Celery will retry:
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 5},
    retry_backoff=True,
)
def send_email_task(
    to_email: str, template_id: str, data: dict, email_type: str
) -> str:
    """
    Background task to send emails via SendGrid.

    Usage in Routers:
    ----------------
    1. Import this task instead of the synchronous send_email:
       from src.tasks.email import send_email_task

    2. Replace the direct call with .delay():
       send_email_task.delay(
           to_email=user.email,
           template_id=settings.SENDGRID_ACTIVATION_TEMPLATE_ID,
           data={"activation_link": link},
           email_type="activation"
       )

    Note: .delay() sends the task to Redis and returns immediately,
    ensuring the API response time is not affected by network latency.
    """
    try:
        sync_send_email(
            to_email=to_email,
            template_id=template_id,
            data=data,
            email_type=email_type,
        )
        msg = f"Email successfully sent to {to_email} with template {template_id}"
        print(msg)
        return msg
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")
        # Re-raise the exception to trigger Celery's autoretry
        raise e
