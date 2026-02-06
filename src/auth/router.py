import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.auth.dependencies import get_current_user, get_current_user_profile
from src.auth.models import (
    User,
    UserGroup,
    UserGroupEnum,
    ActivationTokenModel,
    RefreshTokenModel,
    UserProfileModel,
)
from src.auth.schemas import (
    LoginRequest,
    UserCreate,
    UserResponse,
    TokenLoginResponseSchema,
    UserRegistrationResponseSchema,
    TokenRefreshRequestSchema,
    UserProfileResponse,
    UserProfileCreate,
)
from src.auth.security import (
    create_access_token,
    verify_password,
    generate_secure_token,
)
from src.core.config import settings
from src.core.database import get_async_session
from src.core.s3 import S3Service
from src.core.utils import process_avatar
from src.notifications.email import send_email

router = APIRouter(prefix="/auth", tags=["Authentication"])
s3_service = S3Service()


@router.post(
    "/register",
    response_model=UserRegistrationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user. User must activate account via activation token.",
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

    activation_token_value = generate_secure_token()
    activation_token = ActivationTokenModel(
        user=new_user,
        token=activation_token_value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )

    session.add(new_user)
    session.add(activation_token)
    await session.commit()
    await session.refresh(new_user)

    activation_link = (
        f"http://localhost:8000/api/v1/auth/activate/{activation_token_value}"
    )
    subject = "Movie cinema activate"

    send_email(new_user.email, subject, activation_link)
    return UserRegistrationResponseSchema(
        id=new_user.id,
        email=new_user.email,
        is_active=new_user.is_active,
        activation_token=activation_token_value,
    )


@router.post(
    "/login",
    response_model=TokenLoginResponseSchema,
    summary="Login",
    description="Login and receive access token. Refresh token is issued together.",
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
    refresh_token_value = generate_secure_token()
    refresh_expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    refresh_token = RefreshTokenModel(
        user_id=user.id,
        token=refresh_token_value,
        expires_at=refresh_expires_at,
    )

    session.add(refresh_token)
    await session.commit()

    return TokenLoginResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token_value,
    )


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


@router.post(
    "/refresh",
    response_model=TokenLoginResponseSchema,
    summary="Refresh access token",
    description="Rotate refresh token and issue a new access token",
)
async def refresh_access_token(
    data: TokenRefreshRequestSchema,
    session: AsyncSession = Depends(get_async_session),
):

    result = await session.execute(
        select(RefreshTokenModel)
        .where(RefreshTokenModel.token == data.refresh_token)
        .options(selectinload(RefreshTokenModel.user))
    )
    refresh_token = result.scalar_one_or_none()

    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if refresh_token.expires_at < datetime.now(timezone.utc):
        await session.delete(refresh_token)
        await session.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    user = refresh_token.user

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    await session.delete(refresh_token)

    new_refresh_value = generate_secure_token()
    new_refresh_expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    new_refresh = RefreshTokenModel(
        user_id=user.id,
        token=new_refresh_value,
        expires_at=new_refresh_expires_at,
    )

    session.add(new_refresh)

    new_access_token = create_access_token(user_id=user.id)

    await session.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_value,
        "token_type": "bearer",
    }


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Logout current user and revoke all refresh tokens",
)
async def logout(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    await session.execute(
        delete(RefreshTokenModel).where(RefreshTokenModel.user_id == current_user.id)
    )
    await session.commit()


@router.post(
    "/profile/create",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_profile(
    profile_data: UserProfileCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    existing_profile = await db.execute(
        select(UserProfileModel).where(UserProfileModel.user_id == user.id)
    )
    if existing_profile.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Profile already exists"
        )

    new_profile = UserProfileModel(user_id=user.id, **profile_data.model_dump())
    db.add(new_profile)

    try:
        await db.commit()
        await db.refresh(new_profile)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error creating profile")

    return new_profile


@router.get("/profile", response_model=UserProfileResponse)
async def get_my_profile(profile: UserProfileModel = Depends(get_current_user_profile)):
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_204_NO_CONTENT,
            detail="Profile not found. Please create one first.",
        )

    avatar_url = None
    if profile.avatar:
        avatar_url = await s3_service.generate_presigned_url(profile.avatar)

    response = UserProfileResponse.model_validate(profile)
    response.avatar_url = avatar_url

    return response


@router.patch("/profile/avatar")
async def update_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    profile: UserProfileModel = Depends(get_current_user_profile),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Downloads avatar, deletes old one from S3, updates DB.
    If there is no profile, it throws an error (the user must first create a profile).
    """
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Create profile before uploading avatar.",
        )

    processed_image = process_avatar(file)

    s3_key = f"profiles/{user.id}/{uuid.uuid4()}.webp"

    if profile.avatar:
        await s3_service.delete_file(profile.avatar)

    await s3_service.upload_file(processed_image, s3_key, "image/webp")

    profile.avatar = s3_key
    await db.commit()

    new_avatar_url = await s3_service.generate_presigned_url(s3_key)

    return {"message": "Avatar updated", "avatar_url": new_avatar_url}
