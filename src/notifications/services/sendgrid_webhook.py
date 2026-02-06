from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.models import EmailStatusEnum

from src.auth.models import User

FATAL_EVENTS = {"bounce", "blocked", "dropped"}


class SendGridWebhookService:
    @staticmethod
    async def process_event(event: dict, session: AsyncSession) -> None:
        event_type = event.get("event")

        if event_type not in FATAL_EVENTS:
            return

        email = event.get("email")
        user_id = event.get("custom_args", {}).get("user_id")

        user = None

        if user_id:
            user = await session.get(User, int(user_id))

        if not user and email:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

        if not user:
            return

        user.email_status = EmailStatusEnum.BOUNCED
        user.is_active = False
