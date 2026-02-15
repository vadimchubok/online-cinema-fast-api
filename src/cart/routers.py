from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_role, get_current_user
from src.auth.models import UserGroupEnum
from src.auth.schemas import CurrentUserDTO
from src.cart.exceptions import (
    MovieAlreadyPurchasedException,
    MovieAlreadyInCartException,
    CartIsNotExistException,
    MovieNotInCartException,
    CartIsEmptyException,
)
from src.cart.schemas import MessageSchema, MovieReadSchema, CartItemCreate
from src.core.database import get_async_session
from src.cart.crud import (
    add_movie_to_cart,
    remove_movie,
    clear_cart,
    select_all_movies_from_cart,
)

router = APIRouter(prefix="/cart", tags=["Carts"])

user_permission = Depends(
    require_role(UserGroupEnum.USER, UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)
)
moderator_permission = Depends(
    require_role(UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)
)


@router.post(
    "/movies/",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageSchema,
    dependencies=[user_permission],
)
async def add_movie_to_user_cart(
    cart_item: CartItemCreate,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUserDTO = Depends(get_current_user),
):
    try:
        await add_movie_to_cart(
            db=db,
            movie_id=cart_item.movie_id,
            user_id=current_user.id,
        )
    except (MovieAlreadyPurchasedException, MovieAlreadyInCartException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageSchema(message="Movie successfully added")


@router.delete(
    "/movies/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[user_permission],
)
async def remove_movie_from_cart(
    movie_id: int,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUserDTO = Depends(get_current_user),
):
    try:
        await remove_movie(db=db, movie_id=movie_id, user_id=current_user.id)
    except (CartIsNotExistException, MovieNotInCartException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/movies/",
    dependencies=[user_permission],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_all_movies_from_cart(
    db: Annotated[AsyncSession, Depends(get_async_session)],
    current_user: CurrentUserDTO = Depends(get_current_user),
):
    try:
        await clear_cart(db=db, user_id=current_user.id)
    except (CartIsNotExistException, CartIsEmptyException) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{cart_id}",
    response_model=List[MovieReadSchema],
    dependencies=[user_permission],
    status_code=status.HTTP_200_OK,
)
async def select_all_movies(
    cart_id: int, db: Annotated[AsyncSession, Depends(get_async_session)]
):
    try:
        result = await select_all_movies_from_cart(db=db, cart_id=cart_id)
    except (CartIsNotExistException, CartIsEmptyException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result
