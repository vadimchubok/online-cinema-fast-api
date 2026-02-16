from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.auth.models import User, UserGroupEnum, UserProfileModel
from src.auth.security import decode_access_token
from src.core.database import get_async_session
from src.auth.schemas import CurrentUserDTO
from src.notifications.services.sendgrid_webhook import SendGridWebhookService

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUserDTO:
    """
    Get current user from JWT token WITHOUT database query.

    Parses JWT payload into CurrentUserDTO Pydantic schema.
    This is the main authentication dependency - fast and efficient.

    For cases requiring full SQLAlchemy User object (password operations,
    relationships), use get_full_user() dependency instead.

    Returns:
        CurrentUserDTO: Pydantic model with user data from token

    Raises:
        HTTPException 401: Invalid or expired token
        HTTPException 403: Inactive user
    """

    token = credentials.credentials

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        current_user = CurrentUserDTO(
            id=int(payload["sub"]),
            email=payload["email"],
            user_group=payload["user_group"],
            is_active=payload["is_active"],
        )
    except (KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    return current_user


async def get_full_user(
    current_user: CurrentUserDTO = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """
    Get full SQLAlchemy User object from database.

    Use ONLY when you need:
    - User.verify_password() method
    - User.password setter
    - User relationships (profile, tokens, etc.)

    For most endpoints, get_current_user() is sufficient and faster.

    Args:
        current_user: CurrentUserDTO from JWT token
        session: Database session

    Returns:
        User: Full SQLAlchemy User model from database

    Raises:
        HTTPException 404: User not found in database
    """
    result = await session.execute(
        select(User).options(joinedload(User.group)).where(User.id == current_user.id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


def require_role(*required_roles: UserGroupEnum):
    """
    Dependency factory for checking user's role.

    Works with CurrentUserDTO - no database query needed.
    Checks if current user has one of the required roles.

    Args:
        required_roles: One or more UserGroupEnum values

    Returns:
        CurrentUserDTO if user has required role

    Raises:
        HTTPException 403: Insufficient permissions
    """

    async def role_checker(
        current_user: CurrentUserDTO = Depends(get_current_user),
    ) -> CurrentUserDTO:
        user_role = current_user.user_group
        allowed_roles = [role.value for role in required_roles]

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {allowed_roles}",
            )

        return current_user

    return role_checker


async def get_current_user_profile(
    current_user: CurrentUserDTO = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> UserProfileModel | None:
    """
    Returns the profile of the current user, or None if not created yet.
    """
    query = select(UserProfileModel).where(UserProfileModel.user_id == current_user.id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


def get_user_group(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:
    """
    Extract user group from access token payload.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "user_group" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload["user_group"]


def require_role_from_token(*allowed_roles: UserGroupEnum):
    """
    Dependency factory to check user's role from token payload.
    """

    def role_checker(user_group: str = Depends(get_user_group)):
        if user_group not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[role.value for role in allowed_roles]}",
            )

    return role_checker


def get_sendgrid_service() -> SendGridWebhookService:
    """
    Dependency for get SendGrid webhook service instance.

    Returns:
        SendGridWebhookService: Instance of service for work with SendGrid webhooks
    """
    return SendGridWebhookService()
