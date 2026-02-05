from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_DB_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    DATABASE_URL_ASYNC: str | None = None

    @property
    def database_url_async(self) -> str:
        if self.DATABASE_URL_ASYNC:
            return self.DATABASE_URL_ASYNC

        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB}"
        )

    SECRET_KEY_ACCESS: str = Field(..., env="SECRET_KEY_ACCESS")
    SECRET_KEY_REFRESH: str | None = Field(default=None, env="SECRET_KEY_REFRESH")

    JWT_SIGNING_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
