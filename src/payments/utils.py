from typing import Annotated

import stripe
from fastapi import Request, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User
from src.cart.models import Cart, CartItem
from src.core.config import settings
from src.core.database import get_async_session
from src.notifications.email import send_email
from src.orders.models import Order, OrderStatus, OrderItem
from src.payments.models import Payment, PaymentStatus, PaymentItem


async def resolve_payment(
    request: Request, db: Annotated[AsyncSession, Depends(get_async_session)]
):
    payload = await request.json()
    obj = payload.get("data").get("object")
    metadata = obj.get("metadata")
    if payload.get("type") == "checkout.session.completed":
        user_id = int(metadata.get("user_id"))
        order_id = int(metadata.get("order_id"))
        payment = Payment(
            user_id=user_id,
            order_id=order_id,
            status=PaymentStatus.SUCCESSFUL,
            amount=obj.get("amount_total") / 100,
            external_payment_id=payload.get("id"),
            payment_intent=obj.get("payment_intent"),
        )
        db.add(payment)
        await db.flush()

        order = await db.get(Order, order_id)
        order.status = OrderStatus.PAID

        result = await db.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        order_items = result.scalars().all()

        for item in order_items:
            payment_item = PaymentItem(
                payment_id=payment.id,
                order_item_id=item.id,
                price_at_payment=float(item.price_at_order),
            )
            db.add(payment_item)
        cart = await db.scalar(select(Cart).where(Cart.user_id == user_id))
        if cart:
            await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
            user = await db.get(User, user_id)
            user_email = user.email
            await db.commit()
            send_email(
                to_email=user_email,
                email_type="successful_payment",
                template_id=settings.SENDGRID_PAYMENT_TEMPLATE_ID,
                data={"message": "Your payment is successful"},
            )

    elif payload.get("type") == "refund.created":
        payment_to_refund = await db.scalar(
            select(Payment).where(
                Payment.payment_intent == obj.get("payment_intent")
            )
        )
        print(payment_to_refund)
        if payment_to_refund:
            print(payment_to_refund)
            payment_to_refund.status = PaymentStatus.REFUNDED
            payment_to_refund.external_payment_id = payload.get("id")
            order = await db.get(Order, payment_to_refund.order_id)
            if order:
                order.status = OrderStatus.CANCELED
            await db.commit()


async def create_checkout_session(
    user_id: int | None = None,
    order_id: int | None = None,
    amount: float | None = None,
):
    if not settings.STRIPE_API_KEY:
        raise RuntimeError("STRIPE_API_KEY is not set")
    stripe.api_key = settings.STRIPE_API_KEY
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"Order #{order_id}"},
                    "unit_amount": int(amount * 100),
                },
                "quantity": 1,
            }
        ],
        success_url=f"{settings.FRONTEND_SUCCESS_URL}",
        cancel_url=f"{settings.FRONTEND_CANCEL_URL}",
        metadata={
            "order_id": str(order_id),
            "user_id": str(user_id),
        },
    )
    return session.url
