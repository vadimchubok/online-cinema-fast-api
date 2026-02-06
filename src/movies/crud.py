from typing import Optional, Sequence
from fastapi import HTTPException, status
from sqlalchemy import select, or_, desc, asc, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.movies.models import Movie, Genre, Director, Star, movie_genres, movie_stars
from src.movies.schemas import (
    MovieCreate,
    MovieUpdate,
    GenreCreate,
    GenreUpdate,
    StarCreate,
    StarUpdate,
)
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


async def get_genres_with_counts(
    session: AsyncSession,
) -> Sequence[dict]:
    """
    Retrieve all genres with the count of associated movies.
    Returns a list of dictionaries/objects compatible with GenreReadWithCount.
    """
    stmt = (
        select(Genre, func.count(movie_genres.c.movie_id).label("movie_count"))
        .outerjoin(movie_genres, Genre.id == movie_genres.c.genre_id)
        .group_by(Genre.id)
        .order_by(Genre.name)
    )

    result = await session.execute(stmt)
    rows = result.all()

    return [{**row[0].__dict__, "movie_count": row[1]} for row in rows]


async def get_genre_by_id(session: AsyncSession, genre_id: int) -> Optional[Genre]:
    """
    Retrieve a genre by its ID.
    Returns None if the genre does not exist.
    """
    stmt = select(Genre).where(Genre.id == genre_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_genre(session: AsyncSession, genre_in: GenreCreate) -> Genre:
    """
    Create a new genre.
    Raises HTTP 400 if a genre with the same name already exists.
    """
    new_genre = Genre(name=genre_in.name)
    session.add(new_genre)
    try:
        await session.commit()
        await session.refresh(new_genre)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Genre with this name already exists",
        )
    return new_genre


async def update_genre(
    session: AsyncSession, genre: Genre, genre_update: GenreUpdate
) -> Genre:
    """
    Update an existing genre.
    Only provided fields are updated.
    """
    update_data = genre_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(genre, key, value)

    session.add(genre)
    try:
        await session.commit()
        await session.refresh(genre)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Genre with this name already exists",
        )
    return genre


async def delete_genre(session: AsyncSession, genre: Genre) -> None:
    """
    Delete a genre if it is not assigned to any movie.
    Raises HTTP 400 if the genre is in use.
    """
    stmt = (
        select(movie_genres.c.movie_id)
        .where(movie_genres.c.genre_id == genre.id)
        .limit(1)
    )
    result = await session.execute(stmt)

    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete genre: it is assigned to one or more movies.",
        )
    await session.delete(genre)
    await session.commit()


async def get_stars(
    session: AsyncSession, skip: int = 0, limit: int = 100, search: Optional[str] = None
) -> Sequence[Star]:
    """
    Retrieve a list of stars with optional search and pagination.
    """
    stmt = select(Star)
    if search:
        stmt = stmt.where(Star.name.ilike(f"%{search}%"))

    stmt = stmt.order_by(Star.name).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_star_by_id(session: AsyncSession, star_id: int) -> Optional[Star]:
    """
    Retrieve a star by its ID.
    Returns None if the star does not exist.
    """
    stmt = select(Star).where(Star.id == star_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_star(session: AsyncSession, star_in: StarCreate) -> Star:
    """
    Create a new star.
    Raises HTTP 400 if a star with the same name already exists.
    """
    new_star = Star(name=star_in.name)
    session.add(new_star)
    try:
        await session.commit()
        await session.refresh(new_star)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Star with this name already exists",
        )
    return new_star


async def update_star(
    session: AsyncSession, star: Star, star_update: StarUpdate
) -> Star:
    """
    Update an existing star.
    Only provided fields are updated.
    """
    update_data = star_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(star, key, value)

    session.add(star)
    try:
        await session.commit()
        await session.refresh(star)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Star with this name already exists",
        )
    return star


async def delete_star(session: AsyncSession, star: Star) -> None:
    """
    Delete a star if it is not assigned to any movie.
    Raises HTTP 400 if the star is in use.
    """
    stmt = (
        select(movie_stars.c.movie_id).where(movie_stars.c.star_id == star.id).limit(1)
    )
    result = await session.execute(stmt)

    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete star: they are assigned to one or more movies.",
        )

    await session.delete(star)
    await session.commit()
