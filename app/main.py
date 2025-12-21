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
    # STARTUP - Minimal to ensure fast startup for Cloud Run
    # =========================================================================
    log.info("=" * 60)
    log.info(f"Starting {settings.SERVICE_NAME} v{settings.SERVICE_VERSION}")
    log.info(f"Environment: {settings.ENV}")
    log.info("Fast startup mode enabled - services initialize on first use")
    log.info("=" * 60)
    
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
        log.debug(f"MongoDB disconnect: {e}")
    
    log.info("Shutdown complete")


async def initialize_services():
    """
    Initialize services lazily when first needed.
    
    This runs on first actual request, not during container startup.
    """
    import asyncio
    
    log.info("Initializing services...")
    
    # Run database migrations (synchronous operation)
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, run_migrations)
        log.info("✓ PostgreSQL migrations applied")
    except Exception as e:
        log.warning(f"Migrations failed: {e}")
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, init_db)
            log.info("✓ PostgreSQL initialized")
        except Exception as e2:
            log.error(f"❌ PostgreSQL failed: {e2}")
    
    # Initialize MongoDB
    try:
        await asyncio.wait_for(MongoDBService.connect(), timeout=10.0)
        log.info(f"✓ MongoDB connected: {settings.MONGODB_DB_NAME}")
    except asyncio.TimeoutError:
        log.error("❌ MongoDB timeout")
    except Exception as e:
        log.error(f"❌ MongoDB failed: {e}")


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
    
    # Add startup event to initialize services after server is ready
    @app.on_event("startup")
    async def startup_event():
        """Initialize services after server is listening."""
        import asyncio
        # Run initialization in background, don't await
        asyncio.create_task(initialize_services())
    
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
