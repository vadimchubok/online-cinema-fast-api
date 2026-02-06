from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    POSTGRES_HOST: str = "localhost"
    POSTGRES_DB_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "test_cinema"

    DATABASE_URL_ASYNC: str | None = None

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    AWS_ACCESS_KEY_ID: str = "testing"
    AWS_SECRET_ACCESS_KEY: str = "testing"
    AWS_REGION: str = "eu-central-1"
    S3_BUCKET_NAME: str = "test-bucket"

    @property
    def database_url_async(self) -> str:
        if self.DATABASE_URL_ASYNC:
            return self.DATABASE_URL_ASYNC
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_DB_PORT}/{self.POSTGRES_DB}"
        )

    SECRET_KEY_ACCESS: str = Field(default="super-secret-key", env="SECRET_KEY_ACCESS")
    SECRET_KEY_REFRESH: str | None = Field(default="super-refresh-key", env="SECRET_KEY_REFRESH")

    JWT_SIGNING_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SENDGRID_API_KEY: str | None = None
    EMAIL_FROM: str | None = None
    EMAIL_ENABLED: bool = False

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.test"),
        extra="ignore"
    )


settings = Settings()
