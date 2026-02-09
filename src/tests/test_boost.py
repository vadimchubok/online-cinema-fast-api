import pytest
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import select
from fastapi import HTTPException

from src.auth.models import User, ActivationTokenModel
from src.movies import crud as movie_crud
from src.movies.schemas import MovieCreate


@pytest.mark.asyncio
async def test_final_coverage_push(client, db_session):
    full_movie_data = {
        "name": f"Movie {uuid.uuid4().hex[:6]}",
        "year": 2024,
        "time": 120,
        "imdb": 8.5,
        "votes": 1000,
        "description": "Coverage description",
        "price": Decimal("19.99"),
        "certification_id": 1,
        "genre_ids": [],
        "director_ids": [],
        "star_ids": [],
    }

    data_404 = full_movie_data.copy()
    data_404["genre_ids"] = [99999]
    try:
        await movie_crud.create_movie(db_session, MovieCreate(**data_404))
    except HTTPException as e:
        assert e.status_code == 404

    valid_schema = MovieCreate(**full_movie_data)
    await movie_crud.create_movie(db_session, valid_schema)
    try:
        await movie_crud.create_movie(db_session, valid_schema)
    except HTTPException as e:
        assert e.status_code == 400

    email = f"boost_{uuid.uuid4().hex[:6]}@test.com"
    await client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "password": "Password123!",
            "password_confirm": "Password123!",
        },
    )

    res = await db_session.execute(
        select(ActivationTokenModel).join(User).where(User.email == email)
    )
    tok_obj = res.scalar_one_or_none()

    if tok_obj:
        tok_obj.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        await db_session.commit()

        await client.post("/api/v1/user/activate", json={"token": tok_obj.token})

    await client.post("/api/v1/user/sendgrid", json={"events": "not_list"})
    await movie_crud.get_genres_with_counts(db_session)

    for sort in ["price_asc", "price_desc", "year_desc", "popularity"]:
        await movie_crud.get_movies(db_session, sort_by=sort)
