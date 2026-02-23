import pytest
from src.movies.models import Certification
from sqlalchemy import insert


@pytest.fixture
async def sample_certification(db_session):
    stmt = insert(Certification).values(name="PG-13").returning(Certification.id)
    try:
        res = await db_session.execute(stmt)
        await db_session.commit()
        return res.scalar()
    except Exception:
        from sqlalchemy import select

        res = await db_session.execute(
            select(Certification.id).where(Certification.name == "PG-13")
        )
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
    response = await moderator_client.post("/api/v1/movies", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Inception"


@pytest.mark.integration
async def test_get_movies_list_with_filters(moderator_client):
    filters = [
        {"search": "Inception"},
        {"sort_by": "price_asc"},
        {"sort_by": "year_desc"},
        {"limit": 5},
    ]

    for params in filters:
        response = await moderator_client.get("/api/v1/movies", params=params)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)


@pytest.mark.integration
async def test_get_movie_by_id(moderator_client, sample_certification):
    payload = {
        "name": "Avatar",
        "year": 2009,
        "time": 162,
        "imdb": 7.9,
        "votes": 1200000,
        "description": "Epic film",
        "price": 12.50,
        "certification_id": sample_certification,
    }
    create_res = await moderator_client.post("/api/v1/movies", json=payload)
    movie_id = create_res.json()["id"]

    response = await moderator_client.get(f"/api/v1/movies/{movie_id}/")
    print(response.status_code, response.headers, response.text)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Avatar"


@pytest.mark.integration
async def test_create_movie_forbidden_for_user(client, sample_certification):
    payload = {
        "name": "No Access",
        "year": 2024,
        "certification_id": sample_certification,
    }
    response = await client.post("/api/v1/movies", json=payload)
    assert response.status_code in [401, 403]


@pytest.mark.integration
async def test_update_movie_as_moderator(moderator_client, sample_certification):
    movie_res = await moderator_client.post(
        "/api/v1/movies",
        json={
            "name": "Update Me",
            "year": 2024,
            "time": 120,
            "imdb": 5.0,
            "votes": 100,
            "description": "Desc",
            "price": 10.0,
            "certification_id": sample_certification,
        },
    )
    movie_id = movie_res.json()["id"]

    update_res = await moderator_client.patch(
        f"/api/v1/movies/{movie_id}/", json={"name": "Updated Name"}
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["name"] == "Updated Name"


@pytest.mark.integration
async def test_delete_movie_as_moderator(moderator_client, sample_certification):
    movie_res = await moderator_client.post(
        "/api/v1/movies",
        json={
            "name": "Delete Me",
            "year": 2024,
            "time": 100,
            "imdb": 1.0,
            "votes": 1,
            "description": "X",
            "price": 1.0,
            "certification_id": sample_certification,
        },
    )

    movie_id = movie_res.json()["id"]

    del_res = await moderator_client.delete(f"/api/v1/movies/{movie_id}/")
    assert del_res.status_code in [200, 204]
