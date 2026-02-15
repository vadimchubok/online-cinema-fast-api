import secrets
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import settings
if TYPE_CHECKING:
    from src.auth.models import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against its hashed version.

    This function compares a plain-text password with a hashed password and returns True
    if they match, and False otherwise.

    Args:
        plain_password (str): The plain-text password provided by the user.
        hashed_password (str): The hashed password stored in the database.

    Returns:
        bool: True if the password is correct, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain-text password using the configured password context.

    This function takes a plain-text password and returns its bcrypt hash.
    The bcrypt algorithm is used with a specified number of rounds for enhanced security.

    Args:
        password (str): The plain-text password to hash.

    Returns:
        str: The resulting hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(user: "User" = None) -> str:
    """
    Create JWT access token with full user information.

    Token payload includes: id, email, user_group, is_active.
    This eliminates need for database queries in get_current_user dependency.

    Args:
        user: Full User object with group relationship loaded

    Returns:
        JWT access token string
    """
    expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "sub": str(user.id),
        "email": user.email,
        "user_group": user.group.name,
        "is_active": user.is_active,
        "exp": expire,
        "type": "access"
    }

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY_ACCESS, algorithm=settings.JWT_SIGNING_ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """
    Decode and validate an access token, returning the token's data.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY_ACCESS,
            algorithms=[settings.JWT_SIGNING_ALGORITHM],
        )

        if payload.get("type") != "access":
            return None

        return payload

    except JWTError:
        return None


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using the configured password context.

    This function takes a plain-text password and returns its bcrypt hash.
    The bcrypt algorithm is used with a specified number of rounds for enhanced security.

    Args:
        password (str): The plain-text password to hash.

    Returns:
        str: The resulting hashed password.
    """
    return pwd_context.hash(password)


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token.

    Returns:
        str: Securely generated token.
    """
    return secrets.token_urlsafe(length)
