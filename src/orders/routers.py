from datetime import datetime
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from stripe import StripeError

from src.auth.dependencies import require_role, get_current_user
from src.auth.models import UserGroupEnum, User
from src.cart.exceptions import CartIsEmptyException
from src.core.database import get_async_session
from src.orders.crud import create_order, get_orders, cancel
from src.orders.exceptions import (
    OrderAlreadyPendingException,
    MovieIsNotAvailableException,
    CancellationIsNotAvailable,
    OrderNotFoundException,
)
from src.orders.models import OrderStatus
from src.orders.schemas import OrderRead, MessageSchema, OrderListSchema
from src.payments.utils import create_checkout_session

router = APIRouter(prefix="/order", tags=["Order"])

user_permission = Depends(
    require_role(UserGroupEnum.USER, UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)
)
moderator_permission = Depends(
    require_role(UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)
)


@router.post(
    "/", response_model=OrderRead, status_code=201, dependencies=[user_permission]
)
async def place_new_order(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        result = await create_order(db=db, user=current_user)
    except (
        CartIsEmptyException,
        MovieIsNotAvailableException,
        OrderAlreadyPendingException,
    ) as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        url = await create_checkout_session(
            order_id=result.id, amount=result.total_amount, user_id=current_user.id
        )
    except StripeError as e:
        raise HTTPException(
            status_code=400, detail=f"Payment session creation failed: {e.user_message}"
        )

    return OrderRead(
        id=result.id,
        created_at=result.created_at,
        status=result.status,
        total_amount=result.total_amount,
        items=result.items,
        payment_url=url,
    )


@router.get("/my", response_model=List[OrderListSchema])
async def get_user_orders(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await get_orders(db=db, user_id=current_user.id)


@router.get("/", response_model=list[OrderListSchema], dependencies=[moderator_permission])
async def get_all_orders(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    user_id: int | None = None,
    status: OrderStatus | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    return await get_orders(
        db,
        user_id=user_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )


@router.patch("/{order_id}", response_model=MessageSchema)
async def cancel_order(
    order_id: int, db: Annotated[AsyncSession, Depends(get_async_session)]
):
    try:
        await cancel(db=db, order_id=order_id)
    except (OrderNotFoundException, CancellationIsNotAvailable) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageSchema(message="Order successfully canceled")
