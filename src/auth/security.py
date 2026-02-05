from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import settings


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


def create_access_token(user_id: int) -> str:
    """
    Create a new access token with a default or specified expiration time.
    """
    expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"sub": str(user_id), "exp": expire, "type": "access"}

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
