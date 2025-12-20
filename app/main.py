
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from app.core.config import settings
from pymongo import MongoClient

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__name__)

# MongoDB client
mongo_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    log.info("Starting up...")
    global mongo_client
    try:
        mongo_client = MongoClient(settings.MONGODB_URL)
        # The ismaster command is cheap and does not require auth.
        mongo_client.admin.command('ismaster')
        log.info("MongoDB connection successful.")
    except Exception as e:
        log.error(f"Could not connect to MongoDB: {e}")
        mongo_client = None # Ensure client is None if connection fails
    yield
    # Shutdown
    log.info("Shutting down...")
    if mongo_client:
        mongo_client.close()
        log.info("MongoDB connection closed.")

app = FastAPI(title="AI Microservice", version="0.1.0", lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "ok", "version": "0.1.0", "environment": settings.ENV}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request.state.db = None
    try:
        request.state.db = get_session_local()
        response = await call_next(request)
    finally:
        if request.state.db:
            request.state.db.close()
    return response
