from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import UserGroupEnum
from src.payments.exceptions import PaymentNotFound
from src.payments.models import Payment, PaymentStatus


async def get_payment_by_id(db: AsyncSession, payment_id: int):
    payment = await db.get(Payment, payment_id)
    if not payment:
        raise PaymentNotFound("No payment with such id")
    return payment


async def get_payments(
    db: AsyncSession,
    user_id: int | None = None,
    status: Optional[PaymentStatus] = None,
    payment_id: int | None = None,
    user_group: str = UserGroupEnum.USER,
):
    query = select(Payment)
    if payment_id:
        query = query.where(Payment.id == payment_id)
    if status:
        query = query.where(Payment.status == status)
    if user_group == UserGroupEnum.USER:
        if user_id is None:
            raise ValueError("User ID is required for non-admin")
        query = query.where(Payment.user_id == user_id)
    elif user_id is not None:
        query = query.where(Payment.user_id == user_id)
    query = query.order_by(Payment.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()
