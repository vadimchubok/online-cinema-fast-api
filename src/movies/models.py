import uuid
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


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)

    movies: Mapped[List["Movie"]] = relationship(
        secondary=movie_genres,
        back_populates="genres",
    )