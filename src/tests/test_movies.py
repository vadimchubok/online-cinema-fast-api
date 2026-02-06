import pytest
from src.movies.models import Certification
from sqlalchemy import insert


@pytest.fixture
async def sample_certification(db_session):
    stmt = insert(Certification).values(name="PG-13").returning(Certification.id)
    res = await db_session.execute(stmt)
    await db_session.commit()
    return res.scalar()


@pytest.mark.integration
async def test_create_movie_success(moderator_client, sample_certification):
    payload = {
        "name": "Inception",
        "year": 2010,
        "time": 148,
        "imdb": 8.8,
        "votes": 2400000,
        "description": "A thief who steals corporate secrets...",
        "price": 14.99,
        "certification_id": sample_certification,
    }

    response = await moderator_client.post("/api/v1/movies/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Inception"
    assert "uuid" in data


@pytest.mark.integration
async def test_get_movie_by_id(moderator_client, sample_certification):
    payload = {
        "name": "Avatar",
        "year": 2009,
        "time": 162,
        "imdb": 7.9,
        "votes": 1200000,
        "description": "Epic science fiction film...",
        "price": 12.50,
        "certification_id": sample_certification,
    }
    create_res = await moderator_client.post("/api/v1/movies/", json=payload)
    movie_id = create_res.json()["id"]

    response = await moderator_client.get(f"/api/v1/movies/{movie_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Avatar"


@pytest.mark.integration
async def test_create_movie_forbidden_for_user(
    client, db_session, sample_certification
):
    payload = {
        "name": "No Access",
        "year": 2024,
        "time": 100,
        "imdb": 1.0,
        "votes": 1,
        "description": "...",
        "price": 1.0,
        "certification_id": sample_certification,
    }

    response = await client.post("/api/v1/movies/", json=payload)
    assert response.status_code == 401
