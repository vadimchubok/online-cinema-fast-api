from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List
from decimal import Decimal

from src.orders.models import OrderStatus


class MovieShort(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)


class OrderItemRead(BaseModel):
    movie: MovieShort
    price_at_order: Decimal
    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: int
    created_at: datetime
    status: OrderStatus
    total_amount: Decimal
    items: List[OrderItemRead]
    payment_url: str
    model_config = ConfigDict(from_attributes=True)


class OrderListSchema(BaseModel):
    id: int
    created_at: datetime
    status: OrderStatus
    total_amount: Decimal
    items: List[OrderItemRead]
    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    pass


class MessageSchema(BaseModel):
    message: str
