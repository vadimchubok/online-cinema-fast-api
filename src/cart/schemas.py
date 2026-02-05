from pydantic import BaseModel
from datetime import datetime
from typing import List


class CartItemRead(BaseModel):
    id: int
    movie_id: int
    movie_title: str
    movie_price: float
    added_at: datetime


class CartRead(BaseModel):
    id: int
    user_id: str
    items: List[CartItemRead]
    total_price: float


class CartItemCreate(BaseModel):
    movie_id: int
