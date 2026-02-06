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


class CommentUpdate(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)


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
