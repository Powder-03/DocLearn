
import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

_engine = None
_sessionmaker = None
_lock = threading.Lock()

def get_session_local():
    global _engine, _sessionmaker
    with _lock:
        if _engine is None:
            _engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
            _sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _sessionmaker()
