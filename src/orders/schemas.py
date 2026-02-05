from pydantic import BaseModel
from datetime import datetime
from typing import List
from enum import Enum
from decimal import Decimal


class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"


class OrderItemRead(BaseModel):
    movie_title: str
    price_at_order: Decimal


class OrderRead(BaseModel):
    id: int
    created_at: datetime
    status: OrderStatusEnum
    total_amount: Decimal
    items: List[OrderItemRead]


class OrderCreate(BaseModel):
    pass
