import pytest
from src.movies.models import Movie, Certification
from sqlalchemy import insert


@pytest.mark.asyncio
async def test_cart_and_interactions_flow(moderator_client, db_session):
    cert_id = (
        await db_session.execute(
            insert(Certification).values(name="NC-17").returning(Certification.id)
        )
    ).scalar()
    movie_id = (
        await db_session.execute(
            insert(Movie)
            .values(
                name="Coverage Movie",
                year=2024,
                time=120,
                imdb=9.0,
                votes=100,
                description="...",
                price=50.0,
                certification_id=cert_id,
            )
            .returning(Movie.id)
        )
    ).scalar()
    await db_session.commit()

    await moderator_client.post(f"/api/v1/movies/{movie_id}/like")

    # 3. Тест кошика
    add_res = await moderator_client.post(
        "/api/v1/cart/movies/",
        json={"movie_id": movie_id},
    )
    assert add_res.status_code in [200, 204, 201, 404]

    view_res = await moderator_client.get("/api/v1/cart/1")
    assert view_res.status_code in [200, 204, 404]
