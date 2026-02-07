import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy import select, delete
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
    PasswordResetTokenModel,
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
    ActivationResponse,
    ActivationRequest,
    PasswordResetResponse,
    PasswordChangeSchema,
    PasswordResetConfirmSchema,
    PasswordResetRequestSchema,
    UserProfileUpdate,
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
from src.notifications.services.sendgrid_webhook import SendGridWebhookService
from json import JSONDecodeError
from src.auth.validators import validate_passwords_different

router = APIRouter(prefix="/user", tags=["User"])
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
        f"http://localhost:8000/api/v1/user/activate/{activation_token_value}"
    )

    send_email(
        to_email=new_user.email,
        template_id=settings.SENDGRID_ACTIVATION_TEMPLATE_ID,
        data={"activation_link": activation_link},
        email_type="email_activation",
    )
    return UserRegistrationResponseSchema(
        id=new_user.id,
        email=new_user.email,
        is_active=new_user.is_active,
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


@router.post(
    "/activate",
    response_model=ActivationResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate user account",
    description="Activate user account using activation token from email",
)
async def activate_user(
    data: ActivationRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Activate user account.

    User receives activation token via email after registration.
    This endpoint validates the token and activates the account.
    """
    result = await session.execute(
        select(ActivationTokenModel)
        .where(ActivationTokenModel.token == data.token)
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

    return ActivationResponse(detail="Account successfully activated", email=user.email)


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
    "/password-reset/request",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Send password reset email to user",
)
async def request_password_reset(
    data: PasswordResetRequestSchema,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Request password reset.

    Sends reset token to user's email if account exists.
    Returns success even if email not found (security best practice).
    """
    result = await session.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        return PasswordResetResponse(
            detail="If the email exists, a password reset link has been sent"
        )

    if not user.is_active:
        return PasswordResetResponse(
            detail="If the email exists, a password reset link has been sent"
        )

    await session.execute(
        delete(PasswordResetTokenModel).where(
            PasswordResetTokenModel.user_id == user.id
        )
    )

    reset_token_value = generate_secure_token()
    reset_token = PasswordResetTokenModel(
        user_id=user.id,
        token=reset_token_value,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),  # 1 hour expiry
    )

    session.add(reset_token)
    await session.commit()

    reset_link = (
        f"http://localhost:8000/api/v1/user/password-reset/confirm/{reset_token_value}"
    )

    send_email(
        to_email=user.email,
        template_id=settings.SENDGRID_PASSWORD_RESET_TEMPLATE_ID,
        data={"reset_link": reset_link},
        email_type="password_reset",
    )

    return PasswordResetResponse(
        detail="If the email exists, a password reset link has been sent"
    )


@router.post(
    "/password-reset/confirm",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm password reset",
    description="Reset password using token from email",
)
async def confirm_password_reset(
    data: PasswordResetConfirmSchema,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Confirm password reset.

    Validates reset token and sets new password.
    Token is deleted after successful reset.
    """
    result = await session.execute(
        select(PasswordResetTokenModel)
        .where(PasswordResetTokenModel.token == data.token)
        .options(selectinload(PasswordResetTokenModel.user))
    )
    reset_token = result.scalar_one_or_none()

    if reset_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    if reset_token.expires_at < datetime.now(timezone.utc):
        await session.delete(reset_token)
        await session.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    user = reset_token.user

    user.password = data.new_password

    await session.delete(reset_token)

    await session.execute(
        delete(RefreshTokenModel).where(RefreshTokenModel.user_id == user.id)
    )

    await session.commit()

    return PasswordResetResponse(detail="Password successfully reset")


@router.post(
    "/password-change",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change password for authenticated user",
)
async def change_password(
    data: PasswordChangeSchema,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Change password for authenticated user.

    Requirements:
    - Current password must be correct
    - New password must meet complexity requirements
    - New password must be different from current password
    - Invalidates all refresh tokens after successful change
    """
    if not current_user.verify_password(data.current_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    try:
        validate_passwords_different(
            new_password=data.new_password,
            old_password=None,
            hashed_old_password=current_user.hashed_password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    current_user.password = data.new_password

    await session.execute(
        delete(RefreshTokenModel).where(RefreshTokenModel.user_id == current_user.id)
    )

    await session.commit()

    return PasswordResetResponse(detail="Password successfully changed")


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


@router.patch("/profile", response_model=UserProfileResponse)
async def update_my_profile(
    profile_data: UserProfileUpdate,
    profile: UserProfileModel = Depends(get_current_user_profile),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Partially update user profile.

    Only provided fields will be updated. Null/None values are ignored.
    This endpoint supports partial updates - you can update one or more fields
    without affecting others.

    Updatable fields:
    - first_name
    - last_name
    - date_of_birth
    - info

    Note: Avatar updates should use the dedicated /profile/avatar endpoint.
    """
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Create profile before updating.",
        )

    update_data = profile_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

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


@router.post(
    "/sendgrid",
    status_code=status.HTTP_202_ACCEPTED,
)
async def sendgrid_webhook(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    """Handle SendGrid webhook events."""
    try:
        events = await request.json()
    except JSONDecodeError:
        return {"status": "error", "detail": "Invalid JSON"}

    if not isinstance(events, list):
        return {"status": "error", "detail": "Expected event list"}

    for event in events:
        await SendGridWebhookService.process_event(event, session)

    await session.commit()
    return {"status": "ok"}
