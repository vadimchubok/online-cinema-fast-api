import sendgrid
from sendgrid import CustomArg
from sendgrid.helpers.mail import Mail, Email
from src.core.config import settings

sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)


def send_email(
        *,
        to_email: str,
        template_id: str,
        data: dict,
        email_type: str,
) -> None:
    """Send email via SendGrid with dynamic template."""
    if not settings.SENDGRID_API_KEY:
        raise RuntimeError("SENDGRID_API_KEY is not configured")

    from_email = Email(settings.EMAIL_FROM)
    mail = Mail(from_email=from_email, to_emails=to_email)

    mail.template_id = template_id
    mail.dynamic_template_data = data
    mail.custom_arg = [CustomArg("email_type", email_type)]

    response = sg.client.mail.send.post(request_body=mail.get())

    if response.status_code not in (200, 202):
        raise RuntimeError(f"SendGrid error {response.status_code}: {response.body}")
