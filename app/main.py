"""
Generation Mode Microservice - Main Application.

AI-powered curriculum generation and interactive tutoring service.
"""
import sys
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routers import get_all_routers
from app.db.session import run_migrations, init_db
from app.services.mongodb import MongoDBService

# Configure logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


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
    log.info(f"Planning Model: {settings.PLANNING_MODEL} (Gemini Pro)")
    log.info(f"Tutoring Model: {settings.TUTORING_MODEL} (Gemini Flash)")
    log.info(f"Streaming Threshold: {settings.STREAMING_TOKEN_THRESHOLD} tokens")
    log.info(f"Memory Buffer Size: {settings.MEMORY_BUFFER_SIZE} messages")
    
    # Log startup strategy
    log.info("Fast startup mode: Background initialization of dependencies")
    
    # Check LLM configuration (Gemini only)
    if not settings.GOOGLE_API_KEY:
        log.warning("⚠️  GOOGLE_API_KEY not configured - AI features will not work!")
    else:
        log.info("✓ Google API key configured (Gemini)")
    
    log.info("=" * 60)
    log.info("Service is ready to accept requests")
    log.info("=" * 60)
    
    # Run database setup in background (non-blocking)
    import asyncio
    asyncio.create_task(initialize_services())
    
    yield
    
    # =========================================================================
    # SHUTDOWN
    # =========================================================================
    log.info("Shutting down...")
    
    # Close MongoDB connection
    try:
        await MongoDBService.disconnect()
        log.info("MongoDB connection closed")
    except Exception as e:
        log.warning(f"Error closing MongoDB: {e}")
    
    log.info("Shutdown complete")


async def initialize_services():
    """
    Initialize services in background after app has started.
    
    This prevents blocking the initial startup and allows the container
    to pass health checks quickly on Cloud Run.
    """
    import asyncio
    
    log.info("Starting background service initialization...")
    
    # Run database migrations (synchronous operation)
    try:
        # Run in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, run_migrations)
        log.info("✓ PostgreSQL migrations applied successfully")
    except Exception as e:
        log.warning(f"Alembic migrations failed, falling back to create_all: {e}")
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, init_db)
            log.info("✓ PostgreSQL database initialized with create_all")
        except Exception as e2:
            log.error(f"❌ PostgreSQL database initialization failed: {e2}")
    
    # Initialize MongoDB (required for chat storage)
    try:
        await asyncio.wait_for(MongoDBService.connect(), timeout=10.0)
        log.info(f"✓ MongoDB connected: {settings.MONGODB_DB_NAME}")
    except asyncio.TimeoutError:
        log.error("❌ MongoDB connection timed out after 10 seconds")
        log.warning("⚠️  Chat storage will not work without MongoDB!")
    except Exception as e:
        log.error(f"❌ MongoDB connection failed: {e}")
        log.warning("⚠️  Chat storage will not work without MongoDB!")
    
    log.info("Background service initialization complete")


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
    api_router, health_router, test_router = get_all_routers()
    app.include_router(api_router)
    app.include_router(health_router)
    app.include_router(test_router)
    
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
