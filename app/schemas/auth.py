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
    created_at: Optional[datetime] = None


class AuthResponse(BaseModel):
    """Response model for authentication."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
