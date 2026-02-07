from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional


class PaymentItemSchema(BaseModel):
    id: int
    order_item_id: int
    price_at_payment: float
    model_config = ConfigDict(from_attributes=True)


class PaymentSchema(BaseModel):
    id: int
    user_id: int
    order_id: int
    amount: float
    status: str
    payment_intent: Optional[str]
    external_payment_id: Optional[str]
    created_at: datetime
    items: List[PaymentItemSchema] = []

    model_config = ConfigDict(from_attributes=True)
