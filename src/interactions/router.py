from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.core.database import get_async_session
from src.interactions.models import Favorite, MovieReaction, ReactionType
from src.interactions.schemas import (
    FavoritesListOut,
    MessageOut,
    ReactionSetOut,
    ReactionsSummaryOut,
)
from src.movies.models import Movie

router = APIRouter(prefix="/interactions", tags=["Interactions"])


async def _get_movie_or_404(session: AsyncSession, movie_id: int) -> Movie:
    result = await session.execute(select(Movie).where(Movie.id == movie_id))
    movie = result.scalar_one_or_none()
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Movie not found"
        )
    return movie


@router.post(
    "/favorites/{movie_id}",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add movie to favorites",
)
async def add_to_favorites(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> MessageOut:
    await _get_movie_or_404(session, movie_id)

    result = await session.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.movie_id == movie_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Already in favorites"
        )

    fav = Favorite(user_id=current_user.id, movie_id=movie_id)
    session.add(fav)
    await session.commit()

    return MessageOut(detail="Added to favorites")


@router.delete(
    "/favorites/{movie_id}",
    response_model=MessageOut,
    summary="Remove movie from favorites",
)
async def remove_from_favorites(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> MessageOut:
    result = await session.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.movie_id == movie_id,
        )
    )
    fav = result.scalar_one_or_none()
    if not fav:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Not in favorites"
        )

    await session.delete(fav)
    await session.commit()
    return MessageOut(detail="Removed from favorites")


@router.get(
    "/favorites",
    response_model=FavoritesListOut,
    summary="List favorites (with optional search)",
)
async def list_favorites(
    q: str | None = Query(default=None, description="Search by movie name"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> FavoritesListOut:
    stmt = (
        select(Movie)
        .join(Favorite, Favorite.movie_id == Movie.id)
        .where(Favorite.user_id == current_user.id)
        .order_by(Movie.name.asc())
    )

    if q:
        stmt = stmt.where(Movie.name.ilike(f"%{q}%"))

    result = await session.execute(stmt)
    movies = result.scalars().all()

    return FavoritesListOut(items=movies)


async def _set_reaction(
    session: AsyncSession,
    *,
    user_id: int,
    movie_id: int,
    reaction: ReactionType,
) -> None:
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
        session.add(
            MovieReaction(user_id=user_id, movie_id=movie_id, reaction=reaction)
        )

    await session.commit()


@router.post(
    "/movies/{movie_id}/like",
    response_model=ReactionSetOut,
    summary="Like a movie",
)
async def like_movie(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ReactionSetOut:
    await _get_movie_or_404(session, movie_id)
    await _set_reaction(
        session, user_id=current_user.id, movie_id=movie_id, reaction=ReactionType.LIKE
    )
    return ReactionSetOut(movie_id=movie_id, reaction="LIKE")


@router.post(
    "/movies/{movie_id}/dislike",
    response_model=ReactionSetOut,
    summary="Dislike a movie",
)
async def dislike_movie(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ReactionSetOut:
    await _get_movie_or_404(session, movie_id)
    await _set_reaction(
        session,
        user_id=current_user.id,
        movie_id=movie_id,
        reaction=ReactionType.DISLIKE,
    )
    return ReactionSetOut(movie_id=movie_id, reaction="DISLIKE")


@router.delete(
    "/movies/{movie_id}/reaction",
    response_model=MessageOut,
    summary="Remove my reaction from a movie",
)
async def remove_reaction(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> MessageOut:
    result = await session.execute(
        select(MovieReaction).where(
            MovieReaction.user_id == current_user.id,
            MovieReaction.movie_id == movie_id,
        )
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No reaction to remove"
        )

    await session.delete(existing)
    await session.commit()
    return MessageOut(detail="Reaction removed")


@router.get(
    "/movies/{movie_id}/reactions",
    response_model=ReactionsSummaryOut,
    summary="Get reactions summary for a movie",
)
async def get_reactions_summary(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> ReactionsSummaryOut:
    await _get_movie_or_404(session, movie_id)

    likes_stmt = (
        select(func.count())
        .select_from(MovieReaction)
        .where(
            MovieReaction.movie_id == movie_id,
            MovieReaction.reaction == ReactionType.LIKE,
        )
    )
    dislikes_stmt = (
        select(func.count())
        .select_from(MovieReaction)
        .where(
            MovieReaction.movie_id == movie_id,
            MovieReaction.reaction == ReactionType.DISLIKE,
        )
    )

    likes = (await session.execute(likes_stmt)).scalar_one()
    dislikes = (await session.execute(dislikes_stmt)).scalar_one()

    my_stmt = select(MovieReaction.reaction).where(
        MovieReaction.movie_id == movie_id,
        MovieReaction.user_id == current_user.id,
    )
    my_reaction = (await session.execute(my_stmt)).scalar_one_or_none()

    return ReactionsSummaryOut(
        movie_id=movie_id,
        likes=likes,
        dislikes=dislikes,
        my_reaction=my_reaction.value if my_reaction else None,
    )
