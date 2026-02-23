"""
Interactions repository helpers.

This module contains small reusable functions for Interactions routes:
- fetch entities or raise HTTP 404
- upsert operations for reactions and ratings

The goal is to keep router code cleaner and avoid duplicated queries.
"""


from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.interactions.models import Comment, MovieReaction, Rating, ReactionType
from src.movies.models import Movie


async def get_movie_or_404(session: AsyncSession, movie_id: int) -> Movie:
    """
    Fetch a movie by id or raise HTTP 404.

    Args:
        session: Async SQLAlchemy session.
        movie_id: Movie id.

    Returns:
        Movie instance.

    Raises:
        HTTPException(404): If movie was not found.
    """
    result = await session.execute(select(Movie).where(Movie.id == movie_id))
    movie = result.scalar_one_or_none()
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found",
        )
    return movie


async def get_comment_or_404(session: AsyncSession, comment_id: int) -> Comment:
    """
    Fetch a comment by id or raise HTTP 404.

    Args:
        session: Async SQLAlchemy session.
        comment_id: Comment id.

    Returns:
        Comment instance.

    Raises:
        HTTPException(404): If comment was not found.
    """
    result = await session.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    return comment


async def set_reaction(
    session: AsyncSession,
    *,
    user_id: int,
    movie_id: int,
    reaction: ReactionType,
) -> None:
    """
    Create or update user's reaction for a movie.

    If a reaction already exists for (user_id, movie_id), it will be updated.
    Otherwise a new record will be created.

    Args:
        session: Async SQLAlchemy session.
        user_id: User id.
        movie_id: Movie id.
        reaction: ReactionType (LIKE/DISLIKE).
    """
    result = await session.execute(
        select(MovieReaction).where(
            MovieReaction.user_id == user_id,
            MovieReaction.movie_id == movie_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.reaction = reaction
    else:
        session.add(MovieReaction(user_id=user_id, movie_id=movie_id,
                                  reaction=reaction))

    await session.commit()


async def set_rating(
    session: AsyncSession,
    *,
    user_id: int,
    movie_id: int,
    score: int,
) -> None:
    """
    Create or update user's rating for a movie.

    If a rating already exists for (user_id, movie_id), it will be updated.
    Otherwise a new record will be created.

    Args:
        session: Async SQLAlchemy session.
        user_id: User id.
        movie_id: Movie id.
        score: Rating score (expected 1..10).
    """
    result = await session.execute(
        select(Rating).where(
            Rating.user_id == user_id,
            Rating.movie_id == movie_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.score = score
    else:
        session.add(Rating(user_id=user_id, movie_id=movie_id, score=score))

    await session.commit()
