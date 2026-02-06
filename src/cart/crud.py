from sqlalchemy import select, exists, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.cart.exceptions import MovieAlreadyPurchasedException, \
    MovieAlreadyInCartException, MovieNotInCartException, \
    CartIsNotExistException, CartIsEmptyException
from src.cart.models import Cart, CartItem
from src.movies.models import Movie
from src.orders.models import Order, OrderStatus, OrderItem


async def check_if_user_own_movie(db: AsyncSession,
                                  user_id: int,
                                  movie_id: int) -> bool:
    result = await db.scalar(select(
        exists().where(
            and_(
                Order.user_id == user_id,
                Order.status == OrderStatus.PAID,
                Order.id == OrderItem.order_id,
                OrderItem.movie_id == movie_id,
            )
        )
    ))
    return result


async def get_or_create_cart(db: AsyncSession, user_id: int) -> Cart:
    cart = await db.scalar(
        select(Cart).where(Cart.user_id == user_id)
    )

    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.flush()

    return cart


async def add_movie_to_cart(db: AsyncSession,
                            movie_id: int,
                            user_id: int):
    if await check_if_user_own_movie(db, user_id, movie_id):
        raise MovieAlreadyPurchasedException("You already bought this movie")
    cart = await get_or_create_cart(db, user_id)
    existing_item = await db.scalar(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.movie_id == movie_id,
        )
    )
    if existing_item:
        raise MovieAlreadyInCartException("Movie is already in cart")
    cart_item = CartItem(cart_id=cart.id, movie_id=movie_id)
    db.add(cart_item)
    await db.commit()


async def remove_movie(db: AsyncSession,
                       movie_id: int,
                       user_id: int):
    cart = await db.scalar(
        select(Cart).where(
            Cart.user_id == user_id,
        )
    )
    if not cart:
        raise CartIsNotExistException("You don't have a cart")
    cart_item_in_cart = await db.scalar(
        select(CartItem).
        where(and_(CartItem.movie_id == movie_id, CartItem.cart_id == cart.id)))
    if not cart_item_in_cart:
        raise MovieNotInCartException("This movie is not in your cart")
    await db.delete(cart_item_in_cart)
    await db.commit()


async def select_all_movies_from_cart(db: AsyncSession, user_id: int):
    cart = await db.scalar(
        select(Cart).where(
            Cart.user_id == user_id,
        )
    )
    if not cart:
        raise CartIsNotExistException("You don't have a cart")
    result = await db.scalars(
        select(Movie)
        .join(CartItem, CartItem.movie_id == Movie.id)
        .where(CartItem.cart_id == cart.id)
    )
    if not result:
        raise CartIsEmptyException("Cart is empty")
    return result.all()


async def clear_cart(db: AsyncSession, user_id: int):
    cart = await db.scalar(
        select(Cart).where(
            Cart.user_id == user_id,
        )
    )
    if not cart:
        raise CartIsNotExistException("You don't have a cart")
    cart_items = await db.scalar(
        select(CartItem).where(CartItem.cart_id == cart.id))
    if not cart_items:
        raise CartIsEmptyException("Cart is empty")
    await db.delete(cart_items)
    await db.commit()
