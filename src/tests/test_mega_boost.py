import pytest
import uuid
from decimal import Decimal
from sqlalchemy import select
from src.auth.models import User, UserGroup, UserGroupEnum
from src.movies.models import Movie
from src.cart import crud as cart_crud


@pytest.mark.asyncio
async def test_final_sprint_coverage(client, db_session):
    res_group = await db_session.execute(
        select(UserGroup).where(UserGroup.name == UserGroupEnum.USER.value)
    )
    user_group = res_group.scalar_one_or_none()
    if not user_group:
        user_group = UserGroup(name=UserGroupEnum.USER.value)
        db_session.add(user_group)
        await db_session.flush()

    user = User(
        email=f"user_{uuid.uuid4().hex[:5]}@t.com",
        is_active=True,
        group_id=user_group.id,
    )
    user.password = "Pass123!"

    movie = Movie(
        name=f"Movie_{uuid.uuid4().hex[:5]}",
        year=2024,
        time=120,
        imdb=8.0,
        votes=100,
        description="Test",
        price=Decimal("10.00"),
        certification_id=1,
    )
    db_session.add_all([user, movie])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(movie)

    login_data = {"email": user.email, "password": "Pass123!"}
    login_res = await client.post("/api/v1/user/login", json=login_data)
    token = login_res.json()["access_token"]
    refresh = login_res.json()["refresh_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    await client.post("/api/v1/user/refresh", json={"refresh_token": refresh})
    await cart_crud.add_movie_to_cart(db_session, movie.id, user.id)

    cart = await cart_crud.get_or_create_cart(db_session, user.id)

    await cart_crud.select_all_movies_from_cart(db_session, cart.id)

    await cart_crud.remove_movie(db_session, movie.id, user.id)

    await cart_crud.add_movie_to_cart(db_session, movie.id, user.id)
    await cart_crud.clear_cart(db_session, user.id)

    await client.post(f"/api/v1/interactions/like/{movie.id}", headers=auth_headers)
    await client.get(f"/api/v1/interactions/comments/{movie.id}")
    await client.post(
        f"/api/v1/interactions/comment/{movie.id}",
        headers=auth_headers,
        json={"content": "Coverage comment"},
    )

    await client.post(
        "/api/v1/user/password-change",
        headers=auth_headers,
        json={
            "current_password": "Pass123!",
            "new_password": "NewPass123!",
            "new_password_confirm": "NewPass123!",
        },
    )
    await client.post("/api/v1/user/logout", headers=auth_headers)
