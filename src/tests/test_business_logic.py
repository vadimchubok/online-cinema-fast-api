import pytest
import uuid
from decimal import Decimal
from sqlalchemy import select
from src.auth.models import User, UserGroup, UserGroupEnum
from src.movies.models import Movie
from src.cart.models import Cart, CartItem
from src.orders import crud as order_crud
from src.payments import crud as payment_crud
from src.payments.models import Payment, PaymentStatus


@pytest.mark.asyncio
async def test_order_and_payment_flow(client, db_session):
    res_group = await db_session.execute(
        select(UserGroup).where(UserGroup.name == UserGroupEnum.USER.value)
    )
    user_group = res_group.scalar_one()

    user = User(
        email=f"biz_{uuid.uuid4().hex[:5]}@t.com",
        is_active=True,
        group_id=user_group.id,
    )
    user.password = "Pass123!"

    movie = Movie(
        name=f"Film_{uuid.uuid4().hex[:5]}",
        year=2024,
        time=100,
        imdb=7.0,
        votes=10,
        description="D",
        price=Decimal("100.00"),
        certification_id=1,
    )
    db_session.add_all([user, movie])
    await db_session.flush()

    cart = Cart(user_id=user.id)
    db_session.add(cart)
    await db_session.flush()

    cart_item = CartItem(cart_id=cart.id, movie_id=movie.id)
    db_session.add(cart_item)
    await db_session.commit()
    await db_session.refresh(user)

    order = await order_crud.create_order(db_session, user=user)

    await order_crud.get_orders(db_session, user_id=user.id, status=order.status)

    payment = Payment(
        order_id=order.id,
        user_id=user.id,
        amount=order.total_amount,
        status=PaymentStatus.SUCCESSFUL,
        external_payment_id=f"ext_{uuid.uuid4().hex}",
    )
    db_session.add(payment)
    await db_session.commit()
    await payment_crud.get_payment_by_id(db_session, payment.id)

    await payment_crud.get_payments(
        db_session, user_id=user.id, status=PaymentStatus.SUCCESSFUL
    )

    await payment_crud.get_payments(
        db_session, user_id=user.id, user_group=UserGroupEnum.ADMIN.value
    )

    headers = {"Authorization": f"Bearer {uuid.uuid4().hex}"}
    await client.get("/api/v1/user/me/", headers=headers)
