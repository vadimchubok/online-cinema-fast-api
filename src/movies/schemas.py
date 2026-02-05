from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict


class GenreBase(BaseModel):
    name: str


class GenreRead(GenreBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class StarBase(BaseModel):
    name: str


class StarRead(StarBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class DirectorBase(BaseModel):
    name: str


class DirectorRead(DirectorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class CertificationBase(BaseModel):
    name: str


class CertificationRead(CertificationBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class MovieBase(BaseModel):
    name: str
    year: int
    time: int = Field(..., description="Duration in minutes")
    imdb: float
    votes: int
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: str
    price: Decimal = Field(..., max_digits=10, decimal_places=2)


class MovieCreate(MovieBase):
    certification_id: int
    genre_ids: List[int] = []
    director_ids: List[int] = []
    star_ids: List[int] = []


class MovieUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    time: Optional[int] = None
    imdb: Optional[float] = None
    votes: Optional[int] = None
    meta_score: Optional[float] = None
    gross: Optional[float] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    certification_id: Optional[int] = None
    genre_ids: Optional[List[int]] = None
    director_ids: Optional[List[int]] = None
    star_ids: Optional[List[int]] = None


class MovieRead(MovieBase):
    id: int
    uuid: UUID
    certification: Optional[CertificationRead] = None
    genres: List[GenreRead] = []
    directors: List[DirectorRead] = []
    stars: List[StarRead] = []

    model_config = ConfigDict(from_attributes=True)


class MovieListResponse(BaseModel):
    total: int
    items: List[MovieRead]
