import uuid as uuid_pkg
from typing import List
from sqlalchemy import (
    Table,
    ForeignKey,
    UniqueConstraint,
    DECIMAL,
    Text,
    Column,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from src.core.database import Base


movie_genres = Table(
    "movie_genres",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True),
)

movie_directors = Table(
    "movie_directors",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True),
    Column("director_id", ForeignKey("directors.id"), primary_key=True),
)

movie_stars = Table(
    "movie_stars",
    Base.metadata,
    Column("movie_id", ForeignKey("movies.id"), primary_key=True),
    Column("star_id", ForeignKey("stars.id"), primary_key=True),
)


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)

    movies: Mapped[List["Movie"]] = relationship(
        secondary=movie_genres,
        back_populates="genres",
    )


class Star(Base):
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)

    movies: Mapped[List["Movie"]] = relationship(
        secondary=movie_stars,
        back_populates="stars",
    )


class Director(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)

    movies: Mapped[List["Movie"]] = relationship(
        secondary=movie_directors,
        back_populates="directors",
    )


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)

    movies: Mapped[List["Movie"]] = relationship(
        back_populates="certification",
    )


class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="uq_movie_name_year_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        default=uuid_pkg.uuid4,
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    time: Mapped[int] = mapped_column(nullable=False)
    imdb: Mapped[float] = mapped_column(nullable=False)
    votes: Mapped[int] = mapped_column(nullable=False)

    meta_score: Mapped[float | None]
    gross: Mapped[float | None] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    certification_id: Mapped[int] = mapped_column(
        ForeignKey("certifications.id"),
        nullable=False,
    )
    certification: Mapped["Certification"] = relationship(
        back_populates="movies",
    )
    genres: Mapped[List["Genre"]] = relationship(
        secondary=movie_genres,
        back_populates="movies",
    )
    directors: Mapped[List["Director"]] = relationship(
        secondary=movie_directors,
        back_populates="movies",
    )
    stars: Mapped[List["Star"]] = relationship(
        secondary=movie_stars,
        back_populates="movies",
    )
