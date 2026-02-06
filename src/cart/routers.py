from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_role, get_current_user
from src.auth.models import UserGroupEnum, User
from src.cart.exceptions import MovieAlreadyPurchasedException, \
    MovieAlreadyInCartException, CartIsNotExistException, \
    MovieNotInCartException, CartIsEmptyException
from src.cart.schemas import CartRead, MessageSchema
from src.core.database import get_async_session
from crud import add_movie_to_cart, get_or_create_cart, remove_movie, \
    clear_cart, select_all_movies_from_cart

router = APIRouter(prefix="/cart", tags=["Carts"])

user_permission = Depends(
    require_role(UserGroupEnum.USER, UserGroupEnum.MODERATOR,
                 UserGroupEnum.ADMIN)
)
moderator_permission = Depends(
    require_role(UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN)
)


@router.post("/movies/{movie_id}", response_model=CartRead,
             dependencies=[user_permission])
async def add_movie_to_user_cart(
        movie_id: int,
        db: Annotated[AsyncSession, Depends(get_async_session)],
        current_user: User = Depends(get_current_user)):
    try:
        await add_movie_to_cart(
            db=db,
            movie_id=movie_id,
            user_id=current_user.id,
        )
    except (MovieAlreadyPurchasedException, MovieAlreadyInCartException) as e:
        raise HTTPException(status_code=400, detail=str(e))

    cart = await get_or_create_cart(db, current_user.id)
    return cart


@router.delete("/movies/{movie_id}", response_model=MessageSchema,
               dependencies=[user_permission])
async def remove_movie_from_cart(
        movie_id: int,
        db: Annotated[AsyncSession, Depends(get_async_session)],
        current_user: User = Depends(get_current_user)):
    try:
        await remove_movie(db=db,
                           movie_id=movie_id,
                           user_id=current_user.id)
    except (CartIsNotExistException, MovieNotInCartException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageSchema(message="Movie successfully deleted")


@router.delete("/movies/", response_model=MessageSchema,
               dependencies=[user_permission])
async def remove_all_movies_from_cart(
        db: Annotated[AsyncSession, Depends(get_async_session)],
        current_user: User = Depends(get_current_user)):
    try:
        await clear_cart(db=db,
                         user_id=current_user.id)
    except (CartIsNotExistException, CartIsEmptyException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return MessageSchema(message="Movie successfully deleted")

@router.get("/", response_model=CartRead)
async def select_all_movies(db: Annotated[AsyncSession, Depends(get_async_session)],
        current_user: User = Depends(get_current_user)):
    try:
        result = await select_all_movies_from_cart(db=db,
                         user_id=current_user.id)
    except (CartIsNotExistException, CartIsEmptyException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result

