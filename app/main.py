"""
Generation Mode Microservice - Main Application.

AI-powered curriculum generation and interactive tutoring service.
"""
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient

from app.core.config import settings
from app.api.routers import get_all_routers
from app.db.session import init_db

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# MongoDB client (optional, for future use)
mongo_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    Manages startup and shutdown tasks.
    """
    # =========================================================================
    # STARTUP
    # =========================================================================
    log.info("=" * 60)
    log.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    log.info("=" * 60)
    
    # Log configuration
    log.info(f"Environment: {settings.ENV}")
    log.info(f"Planning Model: {settings.PLANNING_MODEL}")
    log.info(f"Tutoring Model: {settings.TUTORING_MODEL}")
    
    # Initialize database tables
    try:
        init_db()
        log.info("Database initialized successfully")
    except Exception as e:
        log.error(f"Database initialization failed: {e}")
    
    # Initialize MongoDB (optional)
    global mongo_client
    try:
        mongo_client = MongoClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command('ismaster')
        log.info("MongoDB connection successful")
    except Exception as e:
        log.warning(f"MongoDB connection failed (optional): {e}")
        mongo_client = None
    
    # Check LLM configuration
    if not settings.OPENAI_API_KEY and not settings.GOOGLE_API_KEY:
        log.warning("No LLM API keys configured - AI features will not work!")
    else:
        if settings.GOOGLE_API_KEY:
            log.info("Google API key configured ✓")
        if settings.OPENAI_API_KEY:
            log.info("OpenAI API key configured ✓")
    
    log.info("=" * 60)
    log.info("Service is ready to accept requests")
    log.info("=" * 60)
    
    yield
    
    # =========================================================================
    # SHUTDOWN
    # =========================================================================
    log.info("Shutting down...")
    
    if mongo_client:
        mongo_client.close()
        log.info("MongoDB connection closed")
    
    log.info("Shutdown complete")


# =============================================================================
# APPLICATION FACTORY
# =============================================================================

def create_app() -> FastAPI:
    """
    Application factory.
    
    Creates and configures the FastAPI application.
    
    Returns:
        Configured FastAPI instance
    """
    app = FastAPI(
        title="Generation Mode Microservice",
        description="""
## AI-Powered Personalized Learning Platform

This service provides:

- **Dynamic Plan Generation**: Creates personalized, multi-day lesson plans
- **Interactive Tutoring**: Socratic-method teaching with understanding checks
- **Progress Tracking**: Stateful learning across multiple sessions

### Key Endpoints

- `POST /api/v1/sessions` - Create a new learning plan
- `POST /api/v1/chat` - Chat with the AI tutor
- `GET /api/v1/sessions/{id}/plan` - Get lesson plan details
        """,
        version=settings.SERVICE_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    api_router, health_router = get_all_routers()
    app.include_router(api_router)
    app.include_router(health_router)
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with service information."""
        return {
            "service": settings.SERVICE_NAME,
            "version": settings.SERVICE_VERSION,
            "status": "running",
            "environment": settings.ENV,
            "docs": "/docs",
        }
    
    return app


# Create the application instance
app = create_app()
