from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_async_session
from src.movies import crud, schemas
from src.auth.dependencies import require_role
from src.auth.models import User, UserGroupEnum


router = APIRouter(prefix="/stars", tags=["Stars"])


user_permission = Depends(
    require_role(UserGroupEnum.USER, UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)
)

moderator_permission = Depends(
    require_role(UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)
)


@router.get("/", response_model=List[schemas.StarRead])
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


@router.get("/{star_id}", response_model=schemas.StarRead)
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


@router.post("/", response_model=schemas.StarRead, status_code=status.HTTP_201_CREATED)
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


@router.patch("/{star_id}", response_model=schemas.StarRead)
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


@router.delete("/{star_id}", status_code=status.HTTP_204_NO_CONTENT)
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
