import asyncio
from sqlalchemy import select
from src.core.database import async_session_maker
from src.auth.models import UserGroup, UserGroupEnum
from src.movies.models import (
    Genre,
    Director,
    Star,
    Certification,
    Movie,
)


async def seed_data():
    async with async_session_maker() as session:

        for group in UserGroupEnum:
            exists = await session.scalar(
                select(UserGroup).where(UserGroup.name == group.value)
            )
            if not exists:
                session.add(UserGroup(name=group.value))

        cert_names = ["G", "PG", "PG-13", "R", "NC-17"]
        certifications = {}

        for name in cert_names:
            cert = await session.scalar(
                select(Certification).where(Certification.name == name)
            )
            if not cert:
                cert = Certification(name=name)
                session.add(cert)
            certifications[name] = cert

        genre_names = ["Action", "Drama", "Comedy", "Sci-Fi"]
        genres = {}

        for name in genre_names:
            genre = await session.scalar(
                select(Genre).where(Genre.name == name)
            )
            if not genre:
                genre = Genre(name=name)
                session.add(genre)
            genres[name] = genre

        director_names = [
            "Christopher Nolan",
            "Quentin Tarantino",
        ]
        directors = {}

        for name in director_names:
            director = await session.scalar(
                select(Director).where(Director.name == name)
            )
            if not director:
                director = Director(name=name)
                session.add(director)
            directors[name] = director

        star_names = [
            "Leonardo DiCaprio",
            "Brad Pitt",
            "Joseph Gordon-Levitt",
        ]
        stars = {}

        for name in star_names:
            star = await session.scalar(
                select(Star).where(Star.name == name)
            )
            if not star:
                star = Star(name=name)
                session.add(star)
            stars[name] = star

        await session.flush()

        movies_data = [
            {
                "name": "Inception",
                "year": 2010,
                "time": 148,
                "imdb": 8.8,
                "votes": 2400000,
                "meta_score": 74,
                "gross": 829895144,
                "description": "A thief who steals corporate secrets through dream-sharing technology.",
                "price": 9.99,
                "certification": "PG-13",
                "genres": ["Action", "Sci-Fi"],
                "directors": ["Christopher Nolan"],
                "stars": ["Leonardo DiCaprio", "Joseph Gordon-Levitt"],
            },
            {
                "name": "Once Upon a Time in Hollywood",
                "year": 2019,
                "time": 161,
                "imdb": 7.6,
                "votes": 800000,
                "meta_score": 83,
                "gross": 374251247,
                "description": "A faded television actor and his stunt double strive to achieve fame.",
                "price": 8.99,
                "certification": "R",
                "genres": ["Drama", "Comedy"],
                "directors": ["Quentin Tarantino"],
                "stars": ["Leonardo DiCaprio", "Brad Pitt"],
            },
        ]

        for data in movies_data:
            exists = await session.scalar(
                select(Movie).where(
                    Movie.name == data["name"],
                    Movie.year == data["year"],
                )
            )
            if exists:
                continue

            movie = Movie(
                name=data["name"],
                year=data["year"],
                time=data["time"],
                imdb=data["imdb"],
                votes=data["votes"],
                meta_score=data["meta_score"],
                gross=data["gross"],
                description=data["description"],
                price=data["price"],
                certification=certifications[data["certification"]],
            )

            movie.genres = [genres[g] for g in data["genres"]]
            movie.directors = [directors[d] for d in data["directors"]]
            movie.stars = [stars[s] for s in data["stars"]]

            session.add(movie)

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_data())
