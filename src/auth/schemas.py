from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


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
    activation_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequestSchema(BaseModel):
    refresh_token: str
