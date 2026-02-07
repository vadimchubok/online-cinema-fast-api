from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.core.celery_app import celery_app
from src.auth.models import ActivationTokenModel

# --- Sync DB connection for Celery ---
# Since Celery is synchronous, a dedicated engine is required
# (non-asyncpg). Credentials are pulled from settings.

if hasattr(settings, "database_url_sync"):
    SYNC_DATABASE_URL = settings.database_url_sync
else:
    SYNC_DATABASE_URL = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_DB_PORT}/{settings.POSTGRES_DB}"
    )

# Create synchronous engine and session factory
engine = create_engine(SYNC_DATABASE_URL, pool_pre_ping=True)
SessionLocalSync = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task(name="src.tasks.auth.delete_expired_tokens")
def delete_expired_tokens():
    """Periodic task for deleting expired activation tokens.
    Uses a synchronous SQLAlchemy session.
    """
    session = SessionLocalSync()
    try:
        now = datetime.now(timezone.utc)

        deleted_count = (
            session.query(ActivationTokenModel)
            .filter(ActivationTokenModel.expires_at < now)
            .delete()
        )

        session.commit()

        result_msg = (
            f"Cleanup complete. Deleted {deleted_count} expired activation tokens."
        )
        print(result_msg)
        return result_msg

    except Exception as e:
        session.rollback()
        error_msg = f"Error deleting expired tokens: {str(e)}"
        print(error_msg)
        return error_msg

    finally:
        session.close()
