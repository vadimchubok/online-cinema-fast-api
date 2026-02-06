from pydantic import BaseModel, ConfigDict
from typing import List

from src.movies.schemas import GenreRead


class MovieReadSchema(BaseModel):
    name: str
    price: float
    genres: List[GenreRead]
    year: int
    model_config = ConfigDict(from_attributes=True)


class CartItemCreate(BaseModel):
    movie_id: int


class MessageSchema(BaseModel):
    message: str
