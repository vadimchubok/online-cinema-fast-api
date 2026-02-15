from typing import Annotated, List

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import CurrentUserDTO
from src.core.config import settings
from src.auth.dependencies import get_current_user, require_role
from src.auth.models import User, UserGroupEnum
from src.core.database import get_async_session
from src.payments.crud import get_payment_by_id, get_payments
from src.payments.exceptions import PaymentNotFound
from src.payments.models import PaymentStatus
from src.payments.schemas import PaymentSchema

from src.payments.utils import resolve_payment
from stripe import StripeError

router = APIRouter(prefix="/payment", tags=["Payment"])
user_permission = Depends(
    require_role(UserGroupEnum.USER, UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)
)
moderator_permission = Depends(
    require_role(UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)
)


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_async_session)]
):
    await resolve_payment(request, db, background_tasks)
    return {"status": "success"}


@router.post("/{payment_id}/refund")
async def refund_payment(
    payment_id: int, db: Annotated[AsyncSession, Depends(get_async_session)]
):
    stripe.api_key = settings.STRIPE_API_KEY

    try:
        payment = await get_payment_by_id(db, payment_id)
    except PaymentNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

    if not payment.payment_intent:
        print(f"ERROR: Payment {payment_id} has no payment_intent ID in DB")
        raise HTTPException(
            status_code=400,
            detail="Cannot refund: Payment Intent ID is missing in our database",
        )

    try:
        print(f"Attempting Stripe refund for intent: {payment.payment_intent}")

        refund = stripe.Refund.create(payment_intent=payment.payment_intent)

        print(f"Stripe Refund created: {refund.id}")
        return {"status": "refund_initiated", "refund_id": refund.id}

    except StripeError as e:
        error_msg = e.user_message or str(e)
        print(f"STRIPE SDK ERROR: {error_msg}")
        raise HTTPException(status_code=400, detail=f"Refund failed: {error_msg}")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during refund"
        )


@router.get(
    "/my",
    response_model=List[PaymentSchema],
    dependencies=[user_permission],
)
async def get_my_payments(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[CurrentUserDTO, Depends(get_current_user)],
    status: str | None = Query(None, description="Filter by payment status"),
    payment_id: int | None = Query(None, description="Filter by payment ID"),
):
    payments = await get_payments(
        db,
        user_id=current_user.id,
        status=status,
        payment_id=payment_id,
        user_group=UserGroupEnum.USER,
    )
    return payments


@router.get(
    "/",
    response_model=List[PaymentSchema],
    dependencies=[moderator_permission],
)
async def list_all_payments(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    user_id: int | None = Query(None, description="Filter by user_id"),
    status: PaymentStatus | None = Query(None, description="Filter by payment status"),
    payment_id: int | None = Query(None, description="Filter by payment_id"),
):
    payments = await get_payments(
        db,
        user_id=user_id,
        status=status,
        payment_id=payment_id,
        user_group=UserGroupEnum.ADMIN,
    )
    return payments
