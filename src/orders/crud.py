
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.cart.exceptions import CartIsEmptyException
from src.cart.models import Cart
from src.movies.models import Movie
from src.orders.exceptions import UserNotFoundException, \
    MovieIsNotAvailableException, OrderNotFoundException, \
    CancellationIsNotAvailable, OrderAlreadyPendingException

from typing import Optional
from datetime import datetime

from src.orders.models import Order, OrderStatus, OrderItem
from src.payments.models import Payment


from sqlalchemy import select, exists
from sqlalchemy.orm import selectinload
from decimal import Decimal

async def create_order(db: AsyncSession, user: User):
    cart = await db.scalar(
        select(Cart)
        .where(Cart.user_id == user.id)
        .options(selectinload(Cart.items))
    )
    if not cart or not cart.items:
        raise CartIsEmptyException("Cart is empty")

    cart_movie_ids = [item.movie_id for item in cart.items]

    movies = await db.scalars(
        select(Movie).where(Movie.id.in_(cart_movie_ids))
    )
    movies = movies.all()

    existing_movie_ids = {m.id for m in movies}

    missing_movies = [
        item.movie_id for item in cart.items if item.movie_id not in existing_movie_ids
    ]

    if missing_movies:
        raise MovieIsNotAvailableException(
            f"Some movies are no longer available: IDs {missing_movies}"
        )

    pending_exists = await db.scalar(
        select(exists().where(
            Order.user_id == user.id,
            Order.status == OrderStatus.PENDING,
            Order.id == OrderItem.order_id,
            OrderItem.movie_id.in_(cart_movie_ids)
        ))
    )

    if pending_exists:
        raise OrderAlreadyPendingException(
            "You already have a pending order with some of these movies")

    total_amount = sum((movie.price for movie in movies), Decimal("0.00"))

    order = Order(
        user_id=user.id,
        status=OrderStatus.PENDING,
        total_amount=total_amount
    )
    db.add(order)
    await db.flush()

    for movie_id in cart_movie_ids:
        await create_order_item(db=db, order_id=order.id, movie_id=movie_id)

    await db.commit()
    return order

async def create_order_item(db: AsyncSession, order_id: int, movie_id: int):
    order_item = OrderItem(order_id=order_id, movie_id=movie_id)
    db.add(order_item)
    await db.commit()


async def get_orders(
        db: AsyncSession,
        user_id: Optional[int] = None,
        status: Optional[OrderStatus] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
) -> list[Order]:
    stmt = select(Order)

    if user_id is not None:
        stmt = stmt.where(Order.user_id == user_id)

    if status is not None:
        stmt = stmt.where(Order.status == status)

    if date_from is not None:
        stmt = stmt.where(Order.created_at >= date_from)

    if date_to is not None:
        stmt = stmt.where(Order.created_at <= date_to)

    stmt = stmt.order_by(Order.created_at.desc())

    result = await db.scalars(stmt)
    return result.all()

async def cancel(db: AsyncSession, order_id: int):
    order = await db.get(Order, order_id)
    if not order:
        raise OrderNotFoundException("Order with such id doesn't exist")
    payment = await db.scalar(select(Payment).where(Payment.order_id==order.id))
    if payment:
        raise CancellationIsNotAvailable("Cancellation is not possible")
    order.status = OrderStatus.CANCELED
    await db.commit()

