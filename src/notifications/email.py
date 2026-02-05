# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail
# import os
#
#
# def send_email(to_email: str, subject: str, content: str):
#     message = Mail(
#         from_email=os.getenv("SENDGRID_FROM_EMAIL"),
#         to_emails=to_email,
#         subject=subject,
#         html_content=content,
#     )
#
#     try:
#         sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
#         sg.send(message)
#     except Exception as e:
#         raise RuntimeError(f"SendGrid error: {e}")


# import httpx
# from src.core.config import settings
#
# SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
#
#
# class EmailClient:
#     async def send(
#         self,
#         *,
#         to: str,
#         subject: str,
#         html: str,
#     ) -> None:
#         if not settings.EMAIL_ENABLED:
#             print("EMAIL DISABLED")
#             print(f"To: {to}")
#             print(f"Subject: {subject}")
#             print(html)
#             return
#
#         payload = {
#             "personalizations": [
#                 {
#                     "to": [{"email": to}],
#                     "subject": subject,
#                 }
#             ],
#             "from": {"email": settings.EMAIL_FROM},
#             "content": [
#                 {"type": "text/html", "value": html},
#             ],
#         }
#
#         headers = {
#             "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
#             "Content-Type": "application/json",
#         }
#
#         async with httpx.AsyncClient(timeout=10) as client:
#             response = await client.post(
#                 SENDGRID_API_URL,
#                 json=payload,
#                 headers=headers,
#             )
#
#         if response.status_code != 202:
#             raise RuntimeError(
#                 f"SendGrid error {response.status_code}: {response.text}"
#             )
