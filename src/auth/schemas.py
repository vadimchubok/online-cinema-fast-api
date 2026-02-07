from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from src.auth.validators import validate_password_strength


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    group_id: int


class UserRegistrationResponseSchema(BaseModel):
    id: int
    email: EmailStr
    is_active: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequestSchema(BaseModel):
    refresh_token: str


class ActivationRequest(BaseModel):
    """Request schema for account activation."""

    token: str


class ActivationResponse(BaseModel):
    """Response schema for successful activation."""

    detail: str
    email: EmailStr


class PasswordResetRequestSchema(BaseModel):
    """Request schema for password reset."""

    email: EmailStr


class PasswordResetConfirmSchema(BaseModel):
    """Confirm password reset with token and new password."""

    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate password strength at schema level."""
        return validate_password_strength(v)


class PasswordChangeSchema(BaseModel):
    """Change password for authenticated user."""

    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        """Validate password strength at schema level."""
        return validate_password_strength(value)

    @field_validator("new_password")
    @classmethod
    def validate_passwords_not_same(cls, value: str, info) -> str:
        """Ensure new password is different from current password."""
        current_password = info.data.get("current_password")
        if current_password and value == current_password:
            raise ValueError("New password must be different from the current password")
        return value


class PasswordResetResponse(BaseModel):
    """Response for password reset operations."""

    detail: str


class UserProfileBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    info: Optional[str] = None


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileResponse(UserProfileBase):
    id: int
    user_id: int
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    """Schema for partial profile update (PATCH).

    All fields are optional to support partial updates.
    Only provided fields will be updated in the database.
    """

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    info: Optional[str] = None
