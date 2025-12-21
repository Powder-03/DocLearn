"""
MongoDB Test Routes.

Simple endpoints to test MongoDB connectivity without app dependencies.
"""
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.mongodb import MongoDBService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test", tags=["Test"])


class TestMessage(BaseModel):
    """Test message model."""
    message: str


@router.post("/mongodb")
async def test_mongodb_connection(data: TestMessage) -> Dict[str, Any]:
    """
    Test MongoDB connection by writing and reading a document.
    
    This endpoint tests:
    1. MongoDB connection is established
    2. Can write to database
    3. Can read from database
    """
    try:
        # Get database
        db = MongoDBService.get_db()
        
        # Create test document
        test_doc = {
            "test_message": data.message,
            "timestamp": datetime.utcnow(),
            "test_id": f"test_{datetime.utcnow().timestamp()}"
        }
        
        # Insert into test collection
        result = await db.test_collection.insert_one(test_doc)
        
        # Read it back
        retrieved = await db.test_collection.find_one({"_id": result.inserted_id})
        
        # Clean up - delete test document
        await db.test_collection.delete_one({"_id": result.inserted_id})
        
        return {
            "status": "success",
            "mongodb_connected": True,
            "inserted_id": str(result.inserted_id),
            "message": "MongoDB is working correctly",
            "test_data": {
                "sent": data.message,
                "retrieved": retrieved.get("test_message") if retrieved else None
            }
        }
        
    except RuntimeError as e:
        # MongoDB not connected
        return {
            "status": "error",
            "mongodb_connected": False,
            "error": str(e),
            "message": "MongoDB is not connected. Check MONGODB_URL secret."
        }
        
    except Exception as e:
        logger.exception(f"MongoDB test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "mongodb_connected": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )


@router.get("/mongodb/status")
async def mongodb_status() -> Dict[str, Any]:
    """
    Check MongoDB connection status without writing anything.
    
    Quick check to see if MongoDB client is initialized.
    """
    try:
        db = MongoDBService.get_db()
        
        # Try to ping
        result = await db.client.admin.command('ping')
        
        return {
            "status": "connected",
            "mongodb_connected": True,
            "ping_result": result,
            "database": db.name
        }
        
    except RuntimeError as e:
        return {
            "status": "not_connected",
            "mongodb_connected": False,
            "error": str(e),
            "message": "MongoDB client not initialized"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "mongodb_connected": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


@router.get("/ping")
async def simple_ping() -> Dict[str, Any]:
    """
    Simplest possible endpoint - no database, no dependencies.
    
    If this doesn't respond, the FastAPI app itself isn't starting.
    """
    return {
        "status": "ok",
        "message": "FastAPI is running",
        "timestamp": datetime.utcnow().isoformat()
    }
