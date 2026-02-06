from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.movies import crud, schemas
from src.auth.dependencies import require_role
from src.auth.models import User, UserGroupEnum


router = APIRouter(prefix="/movies", tags=["Movies"])
genres_router = APIRouter(prefix="/genres", tags=["Genres"])
stars_router = APIRouter(prefix="/stars", tags=["Stars"])

user_permission = Depends(
    require_role(UserGroupEnum.USER, UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)
)
moderator_permission = Depends(
    require_role(UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)
)


@router.get("/", response_model=List[schemas.MovieRead])
async def read_movies(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    sort_by: Optional[str] = Query(
        None, enum=["price_asc", "price_desc", "year_desc", "popularity"]
    ),
    genre_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_session),
    staff: User = user_permission,
):
    """
    Retrieve a list of movies with filtering, search, sorting, and pagination.
    """

    movies = await crud.get_movies(
        db, skip=skip, limit=limit, search=search, sort_by=sort_by, genre_id=genre_id
    )
    return movies


@router.get("/{movie_id}", response_model=schemas.MovieRead)
async def read_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_async_session),
    staff: User = user_permission,
):
    """
    Retrieve detailed information about a movie by its ID.
    """

    movie = await crud.get_movie_by_id(db, movie_id=movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.post("/", response_model=schemas.MovieRead, status_code=status.HTTP_201_CREATED)
async def create_movie_endpoint(
    movie_in: schemas.MovieCreate,
    db: AsyncSession = Depends(get_async_session),
    staff: User = moderator_permission,
):
    """
    Create a new movie.
    Moderator or admin access required.
    """

    return await crud.create_movie(session=db, movie_in=movie_in)


@router.patch("/{movie_id}", response_model=schemas.MovieRead)
async def update_movie_endpoint(
    movie_id: int,
    movie_update: schemas.MovieUpdate,
    db: AsyncSession = Depends(get_async_session),
    staff: User = moderator_permission,
):
    """
    Update an existing movie.
    Moderator or admin access required.
    """
    movie = await crud.get_movie_by_id(db, movie_id=movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    updated_movie = await crud.update_movie(
        session=db, movie=movie, movie_update=movie_update
    )
    return updated_movie


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie_endpoint(
    movie_id: int,
    db: AsyncSession = Depends(get_async_session),
    staff: User = moderator_permission,
):
    """
    Delete a movie if it has not been purchased.
    Moderator or admin access required.
    """
    movie = await crud.get_movie_by_id(db, movie_id=movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    await crud.delete_movie(session=db, movie=movie)
    return None


@genres_router.get("/", response_model=List[schemas.GenreReadWithCount])
async def read_genres(
    db: AsyncSession = Depends(get_async_session),
    staff: User = user_permission,
):
    """
    Retrieve all genres with the number of movies in each genre.
    """
    return await crud.get_genres_with_counts(db)


@genres_router.post(
    "/", response_model=schemas.GenreRead, status_code=status.HTTP_201_CREATED
)
async def create_genre(
    genre_in: schemas.GenreCreate,
    db: AsyncSession = Depends(get_async_session),
    staff: User = moderator_permission,
):
    """
    Create a new genre.
    Moderator or admin access required.
    """
    return await crud.create_genre(db, genre_in)


@genres_router.patch("/{genre_id}", response_model=schemas.GenreRead)
async def update_genre(
    genre_id: int,
    genre_update: schemas.GenreUpdate,
    db: AsyncSession = Depends(get_async_session),
    staff: User = moderator_permission,
):
    """
    Update an existing genre.
    Moderator or admin access required.
    """
    genre = await crud.get_genre_by_id(db, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return await crud.update_genre(db, genre, genre_update)


@genres_router.delete("/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_async_session),
    staff: User = moderator_permission,
):
    """
    Delete a genre if it is not assigned to any movie.
    Moderator or admin access required.
    """
    genre = await crud.get_genre_by_id(db, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    await crud.delete_genre(db, genre)
    return None


@stars_router.get("/", response_model=List[schemas.StarRead])
async def read_stars(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
    staff: User = user_permission,
):
    """
    Retrieve a list of stars with optional search and pagination.
    """
    return await crud.get_stars(db, skip=skip, limit=limit, search=search)


@stars_router.get("/{star_id}", response_model=schemas.StarRead)
async def read_star(
    star_id: int,
    db: AsyncSession = Depends(get_async_session),
    staff: User = user_permission,
):
    """
    Retrieve detailed information about a star by its ID.
    """
    star = await crud.get_star_by_id(db, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found")
    return star


@stars_router.post(
    "/", response_model=schemas.StarRead, status_code=status.HTTP_201_CREATED
)
async def create_star(
    star_in: schemas.StarCreate,
    db: AsyncSession = Depends(get_async_session),
    staff: User = moderator_permission,
):
    """
    Create a new star.
    Moderator or admin access required.
    """
    return await crud.create_star(db, star_in)


@stars_router.patch("/{star_id}", response_model=schemas.StarRead)
async def update_star(
    star_id: int,
    star_update: schemas.StarUpdate,
    db: AsyncSession = Depends(get_async_session),
    staff: User = moderator_permission,
):
    """
    Update an existing star.
    Moderator or admin access required.
    """
    star = await crud.get_star_by_id(db, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found")
    return await crud.update_star(db, star, star_update)


@stars_router.delete("/{star_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_star(
    star_id: int,
    db: AsyncSession = Depends(get_async_session),
    staff: User = moderator_permission,
):
    """
    Delete a star if it is not assigned to any movie.
    Moderator or admin access required.
    """
    star = await crud.get_star_by_id(db, star_id)
    if not star:
        raise HTTPException(status_code=404, detail="Star not found")
    await crud.delete_star(db, star)
    return None
