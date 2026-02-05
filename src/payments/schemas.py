from typing import List

from pydantic import BaseModel

from src.orders.schemas import OrderRead
from src.payments.models import PaymentStatus


class BasePaymentSchema(BaseModel):
    user_id: int
    order_id: int
    amount: float


class PaymentCreateRequestSchema(BasePaymentSchema):
    pass


class PaymentCreateResponseSchema(BasePaymentSchema):
    id: int
    status: PaymentStatus
    external_payment_id: str | None


class PaymentReadSchema(BasePaymentSchema):
    id: int
    status: PaymentStatus
    order: List[OrderRead]


class ReadPaymentItemSchema(BaseModel):
    id: int
    payment_id: int
    order_item_id: int
    price_at_payment: float
