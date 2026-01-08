"""
Pydantic Schemas for Authentication.

Defines request/response models for auth-related API endpoints.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class RegisterRequest(BaseModel):
    """Request model for user registration."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, max_length=100, description="Password (min 6 chars)")
    name: Optional[str] = Field(None, max_length=100, description="Display name")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "password123",
                "name": "John Doe"
            }
        }


class LoginRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "password123"
            }
        }


class UserResponse(BaseModel):
    """Response model for user information."""
    user_id: str
    email: str
    name: Optional[str] = None
    is_verified: bool = False
    created_at: Optional[datetime] = None


class AuthResponse(BaseModel):
    """Response model for authentication."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


class ChangePasswordRequest(BaseModel):
    """Request model for changing password."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., 
        min_length=6, 
        max_length=100, 
        description="New password (min 6 chars)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newpassword456"
            }
        }


class UpdateProfileRequest(BaseModel):
    """Request model for updating user profile."""
    name: Optional[str] = Field(None, max_length=100, description="Display name")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Jane Doe"
            }
        }


class VerifyEmailRequest(BaseModel):
    """Request model for email verification."""
    token: str = Field(..., description="Email verification token")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123xyz..."
            }
        }


class ResendVerificationRequest(BaseModel):
    """Request model for resending verification email."""
    email: EmailStr = Field(..., description="User's email address")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password."""
    email: EmailStr = Field(..., description="User's email address")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ResetPasswordRequest(BaseModel):
    """Request model for password reset."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(
        ..., 
        min_length=6, 
        max_length=100, 
        description="New password (min 6 chars)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123xyz...",
                "new_password": "newpassword456"
            }
        }
