"""
User Service - MongoDB Implementation.

Business logic for managing users with JWT authentication and email verification.
"""
import uuid
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.services.mongodb import MongoDBService
from app.core.auth import hash_password, verify_password
from app.core.config import settings

logger = logging.getLogger(__name__)


class UserService:
    """
    Service class for managing users with MongoDB.
    """
    
    COLLECTION_NAME = "users"
    TOKENS_COLLECTION = "auth_tokens"
    
    def _get_collection(self):
        """Get the users collection."""
        db = MongoDBService.get_db()
        return db[self.COLLECTION_NAME]
    
    def _get_tokens_collection(self):
        """Get the auth tokens collection."""
        db = MongoDBService.get_db()
        return db[self.TOKENS_COLLECTION]
    
    # =========================================================================
    # USER CRUD
    # =========================================================================
    
    async def create_user(
        self,
        email: str,
        password: str,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new user (unverified).
        
        Args:
            email: User's email address
            password: Plain text password (will be hashed)
            name: Optional display name
            
        Returns:
            Created user document (without password)
            
        Raises:
            ValueError: If email already exists
        """
        collection = self._get_collection()
        
        # Check if email already exists
        existing = await collection.find_one({"email": email.lower()})
        if existing:
            raise ValueError("Email already registered")
        
        user_doc = {
            "user_id": str(uuid.uuid4()),
            "email": email.lower(),
            "password_hash": hash_password(password),
            "name": name,
            "is_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        await collection.insert_one(user_doc)
        
        logger.info(f"Created user {user_doc['user_id']} with email {email}")
        
        return self._user_to_dict(user_doc)
    
    async def authenticate(
        self,
        email: str,
        password: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user by email and password.
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            User document if authenticated, None otherwise
        """
        collection = self._get_collection()
        
        user = await collection.find_one({"email": email.lower()})
        if not user:
            return None
        
        if not verify_password(password, user["password_hash"]):
            return None
        
        logger.info(f"User {user['user_id']} authenticated successfully")
        return self._user_to_dict(user)
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by their ID."""
        collection = self._get_collection()
        user = await collection.find_one({"user_id": user_id})
        return self._user_to_dict(user) if user else None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a user by their email."""
        collection = self._get_collection()
        user = await collection.find_one({"email": email.lower()})
        return self._user_to_dict(user) if user else None
    
    async def update_user(
        self,
        user_id: str,
        name: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update user profile.
        
        Args:
            user_id: User's unique identifier
            name: New display name (optional)
            
        Returns:
            Updated user document or None if not found
        """
        collection = self._get_collection()
        
        update_fields = {"updated_at": datetime.utcnow()}
        
        if name is not None:
            update_fields["name"] = name
        
        result = await collection.find_one_and_update(
            {"user_id": user_id},
            {"$set": update_fields},
            return_document=True,
        )
        
        if result:
            logger.info(f"Updated user {user_id}")
            return self._user_to_dict(result)
        
        return None
    
    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> bool:
        """
        Change user's password.
        
        Args:
            user_id: User's unique identifier
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if password changed, False if current password is wrong
        """
        collection = self._get_collection()
        
        # Get user with password hash
        user = await collection.find_one({"user_id": user_id})
        if not user:
            return False
        
        # Verify current password
        if not verify_password(current_password, user["password_hash"]):
            return False
        
        # Update password
        await collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "password_hash": hash_password(new_password),
                    "updated_at": datetime.utcnow(),
                }
            }
        )
        
        logger.info(f"Password changed for user {user_id}")
        return True
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user account.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if deleted, False if not found
        """
        collection = self._get_collection()
        
        result = await collection.delete_one({"user_id": user_id})
        
        if result.deleted_count > 0:
            # Also delete any tokens
            await self._get_tokens_collection().delete_many({"user_id": user_id})
            logger.info(f"Deleted user {user_id}")
            return True
        
        return False
    
    # =========================================================================
    # EMAIL VERIFICATION
    # =========================================================================
    
    async def create_verification_token(self, user_id: str) -> str:
        """
        Create an email verification token.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Verification token string
        """
        tokens_collection = self._get_tokens_collection()
        
        # Delete any existing verification tokens for this user
        await tokens_collection.delete_many({
            "user_id": user_id,
            "type": "email_verification",
        })
        
        # Create new token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(
            hours=settings.EMAIL_VERIFICATION_EXPIRY_HOURS
        )
        
        await tokens_collection.insert_one({
            "token": token,
            "user_id": user_id,
            "type": "email_verification",
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
        })
        
        logger.info(f"Created verification token for user {user_id}")
        return token
    
    async def verify_email(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify email with token.
        
        Args:
            token: Verification token
            
        Returns:
            User document if verified, None if token invalid/expired
        """
        tokens_collection = self._get_tokens_collection()
        users_collection = self._get_collection()
        
        # Find token
        token_doc = await tokens_collection.find_one({
            "token": token,
            "type": "email_verification",
            "expires_at": {"$gt": datetime.utcnow()},
        })
        
        if not token_doc:
            logger.warning("Invalid or expired verification token")
            return None
        
        # Update user as verified
        from pymongo import ReturnDocument
        result = await users_collection.find_one_and_update(
            {"user_id": token_doc["user_id"]},
            {
                "$set": {
                    "is_verified": True,
                    "verified_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        
        # Delete the used token
        await tokens_collection.delete_one({"_id": token_doc["_id"]})
        
        if result:
            logger.info(f"Email verified for user {result['user_id']}")
            return self._user_to_dict(result)
        
        return None
    
    # =========================================================================
    # PASSWORD RESET
    # =========================================================================
    
    async def create_password_reset_token(self, email: str) -> Optional[str]:
        """
        Create a password reset token.
        
        Args:
            email: User's email address
            
        Returns:
            Reset token string, or None if user not found
        """
        users_collection = self._get_collection()
        tokens_collection = self._get_tokens_collection()
        
        # Find user
        user = await users_collection.find_one({"email": email.lower()})
        if not user:
            return None
        
        user_id = user["user_id"]
        
        # Delete any existing reset tokens for this user
        await tokens_collection.delete_many({
            "user_id": user_id,
            "type": "password_reset",
        })
        
        # Create new token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(
            hours=settings.PASSWORD_RESET_EXPIRY_HOURS
        )
        
        await tokens_collection.insert_one({
            "token": token,
            "user_id": user_id,
            "type": "password_reset",
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
        })
        
        logger.info(f"Created password reset token for user {user_id}")
        return token
    
    async def reset_password(
        self,
        token: str,
        new_password: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Reset password with token.
        
        Args:
            token: Password reset token
            new_password: New password to set
            
        Returns:
            User document if reset successful, None if token invalid/expired
        """
        tokens_collection = self._get_tokens_collection()
        users_collection = self._get_collection()
        
        # Find token
        token_doc = await tokens_collection.find_one({
            "token": token,
            "type": "password_reset",
            "expires_at": {"$gt": datetime.utcnow()},
        })
        
        if not token_doc:
            logger.warning("Invalid or expired password reset token")
            return None
        
        # Update password
        from pymongo import ReturnDocument
        result = await users_collection.find_one_and_update(
            {"user_id": token_doc["user_id"]},
            {
                "$set": {
                    "password_hash": hash_password(new_password),
                    "updated_at": datetime.utcnow(),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        
        # Delete the used token and any other reset tokens
        await tokens_collection.delete_many({
            "user_id": token_doc["user_id"],
            "type": "password_reset",
        })
        
        if result:
            logger.info(f"Password reset for user {result['user_id']}")
            return self._user_to_dict(result)
        
        return None
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _user_to_dict(self, user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert MongoDB document to API response format (excluding password)."""
        if not user:
            return None
        return {
            "user_id": user.get("user_id"),
            "email": user.get("email"),
            "name": user.get("name"),
            "is_verified": user.get("is_verified", False),
            "created_at": user.get("created_at"),
        }


# Singleton instance
user_service = UserService()
