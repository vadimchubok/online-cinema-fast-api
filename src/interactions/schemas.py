from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class FavoriteMovieOut(BaseModel):
    id: int
    name: str
    year: int
    price: Optional[float] = None

    class Config:
        from_attributes = True


class FavoritesListOut(BaseModel):
    items: list[FavoriteMovieOut]


ReactionValue = Literal["LIKE", "DISLIKE"]


class ReactionSetOut(BaseModel):
    movie_id: int
    reaction: ReactionValue


class ReactionsSummaryOut(BaseModel):
    movie_id: int
    likes: int
    dislikes: int
    my_reaction: Optional[ReactionValue] = None


class MessageOut(BaseModel):
    detail: str = Field(..., examples=["OK"])


class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    parent_id: int | None = None


class CommentOut(BaseModel):
    id: int
    user_id: int
    movie_id: int
    parent_id: int | None
    text: str
    created_at: datetime

    class Config:
        from_attributes = True


class CommentsListOut(BaseModel):
    items: list[CommentOut]


class NotificationOut(BaseModel):
    id: int
    type: str
    is_read: bool
    created_at: datetime
    actor_user_id: int | None
    comment_id: int | None

    class Config:
        from_attributes = True


class NotificationsListOut(BaseModel):
    items: list[NotificationOut]


class RatingSetIn(BaseModel):
    score: int = Field(..., ge=1, le=10, examples=[10])


class RatingSetOut(BaseModel):
    movie_id: int
    score: int


class RatingSummaryOut(BaseModel):
    movie_id: int
    average_score: float | None
    votes: int
    my_score: int | None
