from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.movies import crud, schemas
from src.auth.dependencies import require_role
from src.auth.models import User, UserGroupEnum

router = APIRouter(prefix="/genres", tags=["Genres"])


user_permission = Depends(
    require_role(UserGroupEnum.USER, UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)
)

moderator_permission = Depends(
    require_role(UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)
)


@router.get("/", response_model=List[schemas.GenreReadWithCount])
async def read_genres(
    db: AsyncSession = Depends(get_async_session),
    staff: User = user_permission,
):
    """
    Retrieve all genres with the number of movies in each genre.
    """
    return await crud.get_genres_with_counts(db)


@router.post("/", response_model=schemas.GenreRead, status_code=status.HTTP_201_CREATED)
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


@router.patch("/{genre_id}", response_model=schemas.GenreRead)
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


@router.delete("/{genre_id}", status_code=status.HTTP_204_NO_CONTENT)
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
