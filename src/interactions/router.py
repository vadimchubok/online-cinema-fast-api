from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.core.database import get_async_session
from src.interactions.models import (
    Favorite,
    MovieReaction,
    ReactionType,
    Comment,
    Notification,
    NotificationType,
    Rating,
)
from src.interactions.schemas import (
    FavoritesListOut,
    MessageOut,
    ReactionSetOut,
    ReactionsSummaryOut,
    CommentCreate,
    CommentOut,
    CommentsListOut,
    NotificationOut,
    NotificationsListOut,
    RatingSetIn,
    RatingSetOut,
    RatingSummaryOut,
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


async def _get_comment_or_404(session: AsyncSession, comment_id: int) -> Comment:
    result = await session.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    return comment


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
        session,
        user_id=current_user.id,
        movie_id=movie_id,
        reaction=ReactionType.LIKE,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reaction to remove",
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


async def _set_rating(
    session: AsyncSession,
    *,
    user_id: int,
    movie_id: int,
    score: int,
) -> None:
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


@router.post(
    "/movies/{movie_id}/rating",
    response_model=RatingSetOut,
    summary="Set or update my rating for a movie (1-10)",
)
async def set_rating(
    movie_id: int,
    payload: RatingSetIn,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> RatingSetOut:
    await _get_movie_or_404(session, movie_id)
    await _set_rating(
        session,
        user_id=current_user.id,
        movie_id=movie_id,
        score=payload.score,
    )
    return RatingSetOut(movie_id=movie_id, score=payload.score)


@router.delete(
    "/movies/{movie_id}/rating",
    response_model=MessageOut,
    summary="Remove my rating for a movie",
)
async def remove_rating(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> MessageOut:
    await _get_movie_or_404(session, movie_id)

    result = await session.execute(
        select(Rating).where(
            Rating.user_id == current_user.id,
            Rating.movie_id == movie_id,
        )
    )
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No rating to remove",
        )

    await session.delete(existing)
    await session.commit()
    return MessageOut(detail="Rating removed")


@router.get(
    "/movies/{movie_id}/rating",
    response_model=RatingSummaryOut,
    summary="Get rating summary for a movie",
)
async def get_rating_summary(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> RatingSummaryOut:
    await _get_movie_or_404(session, movie_id)

    avg_stmt = select(func.avg(Rating.score)).where(Rating.movie_id == movie_id)
    votes_stmt = (
        select(func.count()).select_from(Rating).where(Rating.movie_id == movie_id)
    )

    average_score = (await session.execute(avg_stmt)).scalar_one()
    votes = (await session.execute(votes_stmt)).scalar_one()

    my_stmt = select(Rating.score).where(
        Rating.movie_id == movie_id,
        Rating.user_id == current_user.id,
    )
    my_score = (await session.execute(my_stmt)).scalar_one_or_none()

    return RatingSummaryOut(
        movie_id=movie_id,
        average_score=float(average_score) if average_score is not None else None,
        votes=votes,
        my_score=my_score,
    )


@router.post(
    "/movies/{movie_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create comment for a movie (flat list, but parent_id allowed)",
)
async def create_comment(
    movie_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> CommentOut:
    await _get_movie_or_404(session, movie_id)

    parent: Comment | None = None
    if payload.parent_id is not None:
        parent = await _get_comment_or_404(session, payload.parent_id)
        if parent.movie_id != movie_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent comment belongs to another movie",
            )

    comment = Comment(
        user_id=current_user.id,
        movie_id=movie_id,
        parent_id=payload.parent_id,
        text=payload.text,
    )
    session.add(comment)
    await session.flush()

    if parent is not None and parent.user_id != current_user.id:
        session.add(
            Notification(
                recipient_user_id=parent.user_id,
                actor_user_id=current_user.id,
                comment_id=comment.id,
                type=NotificationType.COMMENT_REPLY,
            )
        )
    await session.commit()
    await session.refresh(comment)
    return CommentOut.model_validate(comment)


@router.get(
    "/movies/{movie_id}/comments",
    response_model=CommentsListOut,
    summary="List comments for a movie (flat)",
)
async def list_comments(
    movie_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
) -> CommentsListOut:
    await _get_movie_or_404(session, movie_id)

    stmt = (
        select(Comment)
        .where(Comment.movie_id == movie_id)
        .order_by(Comment.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    comments = result.scalars().all()

    return CommentsListOut(items=[CommentOut.model_validate(c) for c in comments])


@router.delete(
    "/comments/{comment_id}",
    response_model=MessageOut,
    summary="Delete my comment",
)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> MessageOut:
    comment = await _get_comment_or_404(session, comment_id)

    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can delete only your own comments",
        )

    await session.delete(comment)
    await session.commit()
    return MessageOut(detail="Comment deleted")


@router.get(
    "/notifications",
    response_model=NotificationsListOut,
    summary="List my notifications",
)
async def list_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> NotificationsListOut:
    stmt = (
        select(Notification)
        .where(Notification.recipient_user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await session.execute(stmt)
    notifications = result.scalars().all()

    return NotificationsListOut(
        items=[NotificationOut.model_validate(n) for n in notifications]
    )


@router.patch(
    "/notifications/{notification_id}/read",
    response_model=MessageOut,
    summary="Mark notification as read",
)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> MessageOut:
    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.recipient_user_id == current_user.id,
        )
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notification.is_read = True
    await session.commit()

    return MessageOut(detail="Notification marked as read")
