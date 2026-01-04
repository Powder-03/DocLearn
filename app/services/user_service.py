"""
User Service - MongoDB Implementation.

Business logic for managing users with simple JWT authentication.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from app.services.mongodb import MongoDBService
from app.core.auth import hash_password, verify_password

logger = logging.getLogger(__name__)


class UserService:
    """
    Service class for managing users with MongoDB.
    """
    
    COLLECTION_NAME = "users"
    
    def _get_collection(self):
        """Get the users collection."""
        db = MongoDBService.get_db()
        return db[self.COLLECTION_NAME]
    
    async def create_user(
        self,
        email: str,
        password: str,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new user.
        
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
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        await collection.insert_one(user_doc)
        
        logger.info(f"Created user {user_doc['user_id']} with email {email}")
        
        # Return without password
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
    
    def _user_to_dict(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to API response format (excluding password)."""
        if not user:
            return None
        return {
            "user_id": user.get("user_id"),
            "email": user.get("email"),
            "name": user.get("name"),
            "created_at": user.get("created_at"),
        }


# Singleton instance
user_service = UserService()
