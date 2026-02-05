from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.movies import crud, schemas
from src.auth.dependencies import get_current_user, require_role
from src.auth.models import User, UserGroupEnum


router = APIRouter(prefix="/movies", tags=["Movies"])

user_permission = Depends(require_role(UserGroupEnum.USER, UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN))
moderator_permission = Depends(require_role(UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN))


@router.get("/", response_model=List[schemas.MovieRead])
async def read_movies(
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        sort_by: Optional[str] = Query(None, enum=["price_asc", "price_desc", "year_desc", "popularity"]),
        genre_id: Optional[int] = None,
        db: AsyncSession = Depends(get_async_session),
        staff: User = user_permission
):

    movies = await crud.get_movies(
        db, skip=skip, limit=limit, search=search, sort_by=sort_by, genre_id=genre_id
    )
    return movies


@router.get("/{movie_id}", response_model=schemas.MovieRead)
async def read_movie(
        movie_id: int,
        db: AsyncSession = Depends(get_async_session),
        staff: User = user_permission
):

    movie = await crud.get_movie_by_id(db, movie_id=movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.post("/", response_model=schemas.MovieRead, status_code=status.HTTP_201_CREATED)
async def create_movie_endpoint(
        movie_in: schemas.MovieCreate,
        db: AsyncSession = Depends(get_async_session),
        staff: User = moderator_permission
):

    return await crud.create_movie(session=db, movie_in=movie_in)


@router.put("/{movie_id}", response_model=schemas.MovieRead)
async def update_movie_endpoint(
        movie_id: int,
        movie_update: schemas.MovieUpdate,
        db: AsyncSession = Depends(get_async_session),
        staff: User = moderator_permission
):
    movie = await crud.get_movie_by_id(db, movie_id=movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    updated_movie = await crud.update_movie(session=db, movie=movie, movie_update=movie_update)
    return updated_movie


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie_endpoint(
        movie_id: int,
        db: AsyncSession = Depends(get_async_session),
        staff: User = moderator_permission
):
    movie = await crud.get_movie_by_id(db, movie_id=movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    #moviebuy

    await crud.delete_movie(session=db, movie=movie)
    return None