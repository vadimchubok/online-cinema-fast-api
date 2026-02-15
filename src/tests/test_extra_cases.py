import pytest
import uuid
from decimal import Decimal
from sqlalchemy import select
from src.auth.models import User, UserGroup, UserGroupEnum
from src.movies.models import Movie
from src.auth.security import create_access_token


@pytest.mark.asyncio
async def test_additional_app_logic(client, db_session):
    res_group = await db_session.execute(
        select(UserGroup).where(UserGroup.name == UserGroupEnum.USER.value)
    )
    user_group = res_group.scalar_one()

    user = User(
        email=f"test_user_{uuid.uuid4().hex[:5]}@example.com",
        is_active=True,
        group_id=user_group.id,
    )
    user.password = "SecurePass123!"

    movie = Movie(
        name=f"Movie_{uuid.uuid4().hex[:5]}",
        year=2024,
        time=90,
        imdb=7.5,
        votes=50,
        description="Test Movie",
        price=Decimal("12.50"),
        certification_id=1,
    )
    db_session.add_all([user, movie])
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(movie)

    await db_session.refresh(user, ["group"])
    token = create_access_token(user=user)
    headers = {"Authorization": f"Bearer {token}"}

    await client.get("/api/v1/user/me", headers=headers)
    await client.post("/api/v1/user/password-reset", json={"email": user.email})

    await client.post(f"/api/v1/cart/add/{movie.id}", headers=headers)
    await client.get("/api/v1/cart/", headers=headers)
    await client.delete(f"/api/v1/cart/remove/{movie.id}", headers=headers)

    movie_update_data = {"name": "Updated Name"}
    await client.patch(
        f"/api/v1/movies/{movie.id}", json=movie_update_data, headers=headers
    )
    await client.delete(f"/api/v1/movies/{movie.id}", headers=headers)

    await client.get(f"/api/v1/interactions/comments/{movie.id}")
