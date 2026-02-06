from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.auth.models import User, UserGroupEnum, UserProfileModel
from src.auth.security import decode_access_token
from src.core.database import get_async_session


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """
    Dependency get current user from JWT token.
    This is the main authentication dependency used by all protected endpoints
    across the application. Other developers should use this dependency to
    access the current user in their endpoints.
    """

    token = credentials.credentials

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await session.execute(
        select(User).options(joinedload(User.group)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    return user


def require_role(*required_roles: UserGroupEnum):
    """
    Dependency factory for checking user's role.
    Creates a dependency that checks if the current user has one of the
    required roles. Used for endpoints that should only be accessible to
    admins or moderators.
    """

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not current_user.group:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User group not assigned"
            )

        user_role = current_user.group.name
        allowed_roles = [role.value for role in required_roles]

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {allowed_roles}",
            )

        return current_user

    return role_checker


async def get_current_user_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
) -> UserProfileModel | None:
    """
    Returns the profile of the current user, or None if not created yet.
    """
    query = select(UserProfileModel).where(UserProfileModel.user_id == user.id)
    result = await db.execute(query)
    return result.scalar_one_or_none()
