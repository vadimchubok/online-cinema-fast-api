from typing import Optional, Sequence
from fastapi import HTTPException, status
from sqlalchemy import select, or_, desc, asc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.movies.models import Movie, Genre, Director, Star
from src.movies.schemas import MovieCreate, MovieUpdate
from src.orders.models import OrderItem, Order, OrderStatus


async def check_movie_purchased(session: AsyncSession, movie_id: int) -> bool:
    """
    Check whether a movie has been purchased in any paid order.
    Returns True if the movie exists in at least one PAID order,
    otherwise returns False.
    """
    stmt = (
        select(OrderItem.id)
        .join(Order)
        .where(OrderItem.movie_id == movie_id, Order.status == OrderStatus.PAID)
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_movie_by_id(session: AsyncSession, movie_id: int) -> Optional[Movie]:
    """
    Retrieve a movie by its ID with all related entities loaded.

    Loads genres, directors, stars, and certification.
    Returns None if the movie does not exist.
    """
    query = (
        select(Movie)
        .where(Movie.id == movie_id)
        .options(
            selectinload(Movie.genres),
            selectinload(Movie.directors),
            selectinload(Movie.stars),
            selectinload(Movie.certification),
        )
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_movies(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    genre_id: Optional[int] = None,
) -> Sequence[Movie]:
    """
    Retrieve a list of movies with optional filtering, searching, and sorting.

    Supports pagination, text search, genre filtering, and multiple
    sorting strategies (price, year, popularity).
    """
    query = select(Movie).options(
        selectinload(Movie.genres),
        selectinload(Movie.directors),
        selectinload(Movie.stars),
        selectinload(Movie.certification),
    )

    if genre_id:
        query = query.where(Movie.genres.any(Genre.id == genre_id))

    if search:
        search_filter = or_(
            Movie.name.ilike(f"%{search}%"),
            Movie.description.ilike(f"%{search}%"),
            Movie.stars.any(Star.name.ilike(f"%{search}%")),
            Movie.directors.any(Director.name.ilike(f"%{search}%")),
        )
        query = query.where(search_filter)

    if sort_by == "price_asc":
        query = query.order_by(asc(Movie.price))
    elif sort_by == "price_desc":
        query = query.order_by(desc(Movie.price))
    elif sort_by == "year_desc":
        query = query.order_by(desc(Movie.year))
    elif sort_by == "popularity":
        query = query.order_by(desc(Movie.votes))
    else:
        query = query.order_by(desc(Movie.id))

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


async def create_movie(session: AsyncSession, movie_in: MovieCreate) -> Movie:
    """
    Create a new movie and assign related genres, directors, and stars.

    Raises HTTP 404 if any related entity does not exist.
    Raises HTTP 400 if a unique constraint is violated.
    """
    data = movie_in.model_dump(exclude={"genre_ids", "director_ids", "star_ids"})
    new_movie = Movie(**data)

    if movie_in.genre_ids:
        genres_result = await session.execute(
            select(Genre).where(Genre.id.in_(movie_in.genre_ids))
        )
        genres = genres_result.scalars().all()
        if len(genres) != len(movie_in.genre_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more genres not found",
            )
        new_movie.genres = list(genres)

    if movie_in.director_ids:
        directors_result = await session.execute(
            select(Director).where(Director.id.in_(movie_in.director_ids))
        )
        directors = directors_result.scalars().all()
        if len(directors) != len(movie_in.director_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more directors not found",
            )
        new_movie.directors = list(directors)

    if movie_in.star_ids:
        stars_result = await session.execute(
            select(Star).where(Star.id.in_(movie_in.star_ids))
        )
        stars = stars_result.scalars().all()
        if len(stars) != len(movie_in.star_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more stars not found",
            )
        new_movie.stars = list(stars)

    session.add(new_movie)

    try:
        await session.commit()
        await session.refresh(new_movie)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie with this name, year, and time already exists",
        )

    return await get_movie_by_id(session, new_movie.id)


async def update_movie(
    session: AsyncSession, movie: Movie, movie_update: MovieUpdate
) -> Movie:
    """
    Update an existing movie and its related entities.

    Only provided fields are updated.
    Raises HTTP 404 if related entities are not found.
    """
    update_data = movie_update.model_dump(exclude_unset=True)

    if "genre_ids" in update_data:
        genre_ids = update_data.pop("genre_ids")
        genres_result = await session.execute(
            select(Genre).where(Genre.id.in_(genre_ids))
        )
        genres = genres_result.scalars().all()
        if len(genres) != len(genre_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more genres not found",
            )
        movie.genres = list(genres)

    if "director_ids" in update_data:
        director_ids = update_data.pop("director_ids")
        directors_result = await session.execute(
            select(Director).where(Director.id.in_(director_ids))
        )
        directors = directors_result.scalars().all()
        if len(directors) != len(director_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more directors not found",
            )
        movie.directors = list(directors)

    if "star_ids" in update_data:
        star_ids = update_data.pop("star_ids")
        stars_result = await session.execute(select(Star).where(Star.id.in_(star_ids)))
        stars = stars_result.scalars().all()
        if len(stars) != len(star_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more stars not found",
            )
        movie.stars = list(stars)

    for key, value in update_data.items():
        setattr(movie, key, value)

    session.add(movie)

    try:
        await session.commit()
        await session.refresh(movie)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Update failed due to unique constraint violation",
        )

    return await get_movie_by_id(session, movie.id)


async def delete_movie(session: AsyncSession, movie: Movie) -> None:
    """
    Delete a movie if it has not been purchased by any user.

    Raises HTTP 400 if the movie exists in a paid order.
    """
    if await check_movie_purchased(session, movie.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete movie: it has already been purchased by users.",
        )
    await session.delete(movie)
    await session.commit()
