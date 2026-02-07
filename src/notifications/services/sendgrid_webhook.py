import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.models import User

logger = logging.getLogger(__name__)

FATAL_EVENTS = {"bounce", "blocked", "dropped", "spamreport"}


class SendGridWebhookService:
    @staticmethod
    async def _handle_activation_email_failure(
        email: str,
        event_type: str,
        reason: str | None,
        session: AsyncSession,
    ) -> None:
        """Delete unactivated user or log warning for active user."""
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            return

        if not user.is_active:
            await session.delete(user)
            logger.warning(
                "Deleted unactivated user due to email failure",
                extra={"email": email, "event": event_type, "reason": reason},
            )
        else:
            logger.error(
                "Email delivery failed for active user",
                extra={"email": email, "event": event_type, "reason": reason},
            )

    @staticmethod
    async def _handle_payment_email_failure(
            email: str,
            session: AsyncSession,
    ) -> None:
        """
        Log payment notification delivery failure.

        Payment is already processed, so we only log the issue.
        User can still see order details in their account.
        """
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            return


    @staticmethod
    async def process_event(event: dict, session: AsyncSession) -> None:
        """Process SendGrid webhook event."""
        event_type = event.get("event")

        if event_type not in FATAL_EVENTS:
            return

        email = event.get("email")
        if not email:
            return

        reason = event.get("reason") or event.get("response")

        email_type = event.get("email_type")

        if email_type == "email_activation":
            await SendGridWebhookService._handle_activation_email_failure(
                email, event_type, reason, session
            )

        if email_type == "successful_payment":
            await SendGridWebhookService._handle_payment_email_failure(
                email, session
            )
