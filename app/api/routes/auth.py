"""
Authentication Routes.

API endpoints for user registration, login, and profile management.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException

from app.services.user_service import user_service, UserService
from app.core.auth import create_access_token, get_current_user, AuthUser
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
    MessageResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_user_service() -> UserService:
    """Get UserService instance."""
    return user_service


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    request: RegisterRequest,
    service: UserService = Depends(get_user_service),
):
    """
    Register a new user.
    
    Creates a new user account and returns an access token.
    
    **Request Body:**
    - `email`: Valid email address
    - `password`: Password (min 6 characters)
    - `name`: Optional display name
    """
    try:
        user = await service.create_user(
            email=request.email,
            password=request.password,
            name=request.name,
        )
        
        # Create access token
        token = create_access_token(
            user_id=user["user_id"],
            email=user["email"],
            name=user.get("name"),
        )
        
        return AuthResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(
                user_id=user["user_id"],
                email=user["email"],
                name=user.get("name"),
                created_at=user.get("created_at"),
            ),
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    service: UserService = Depends(get_user_service),
):
    """
    Login with email and password.
    
    Returns an access token on successful authentication.
    """
    user = await service.authenticate(
        email=request.email,
        password=request.password,
    )
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Create access token
    token = create_access_token(
        user_id=user["user_id"],
        email=user["email"],
        name=user.get("name"),
    )
    
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            user_id=user["user_id"],
            email=user["email"],
            name=user.get("name"),
            created_at=user.get("created_at"),
        ),
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: AuthUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    """
    Get current user's profile.
    
    Requires authentication.
    """
    user = await service.get_user_by_id(current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        name=user.get("name"),
        created_at=user.get("created_at"),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Logout current user.
    
    Note: Since we use stateless JWT, this is just a confirmation.
    The client should discard the token.
    """
    return MessageResponse(message="Successfully logged out")
