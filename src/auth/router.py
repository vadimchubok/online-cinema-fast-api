from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.dependencies import get_current_user
from src.auth.models import User, UserGroup, UserGroupEnum, ActivationTokenModel
from src.auth.schemas import LoginRequest, Token, UserCreate, UserResponse
from src.auth.security import (
    create_access_token,
    verify_password,
    generate_secure_token,
)
from src.core.database import get_async_session

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user. MVP version: user is active immediately.",
)
async def register(
    user_data: UserCreate, session: AsyncSession = Depends(get_async_session)
):
    """
    Register new user
    """
    result = await session.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    result = await session.execute(
        select(UserGroup).where(UserGroup.name == UserGroupEnum.USER.value)
    )
    user_group = result.scalar_one_or_none()

    if not user_group:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User group not found. Please run database migrations first.",
        )

    new_user = User(
        email=str(user_data.email),
        group_id=user_group.id,
    )
    new_user.password = user_data.password

    token_value = generate_secure_token()
    activation_token = ActivationTokenModel(
        user=new_user,
        token=token_value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )

    session.add(new_user)
    session.add(activation_token)
    await session.commit()
    await session.refresh(new_user)
    token_value = generate_secure_token()

    activation_link = f"http://localhost:8000/api/v1/auth/activate/{token_value}"
    print(activation_link)

    return new_user


@router.post(
    "/login",
    response_model=Token,
    summary="Login",
    description="Login with email and password to get access token",
)
async def login(
    credentials: LoginRequest, session: AsyncSession = Depends(get_async_session)
):
    """
    User login
    """
    result = await session.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    access_token = create_access_token(user_id=user.id)

    return Token(access_token=access_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about currently authenticated user",
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get info about current user
    """
    return current_user


@router.get(
    "/activate/{token}",
    summary="Activate user account",
    description="Activate user account using activation token",
)
async def activate_user(
    token: str,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(ActivationTokenModel)
        .where(ActivationTokenModel.token == token)
        .options(selectinload(ActivationTokenModel.user))
    )

    activation_token = result.scalar_one_or_none()

    if activation_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid activation token",
        )

    if activation_token.expires_at < datetime.now(timezone.utc):
        await session.delete(activation_token)
        await session.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation token has expired",
        )

    user = activation_token.user

    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already activated",
        )

    user.is_active = True
    await session.delete(activation_token)

    await session.commit()

    return {"detail": "Account successfully activated"}

