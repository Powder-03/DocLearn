"""
Health Check Routes.

API endpoints for service health monitoring.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.deps import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns service status and version information.
    """
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "environment": settings.ENV,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check endpoint.
    
    Verifies database connectivity and returns detailed status.
    """
    checks = {
        "database": False,
        "llm_config": False,
    }
    
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database check failed: {str(e)}")
    
    # Check LLM configuration
    checks["llm_config"] = bool(
        settings.OPENAI_API_KEY or settings.GOOGLE_API_KEY
    )
    
    all_healthy = all(checks.values())
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check endpoint.
    
    Simple check to verify the service is running.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
    }
