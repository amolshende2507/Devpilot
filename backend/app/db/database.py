from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Configure the engine with pessimistic connection pool limits
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # Automatically heals dropped or dead connections
    pool_recycle=300,        # Recycles inactive connections older than 5 minutes
    pool_size=5,             # Standard persistent connection pool size
    max_overflow=10          # Transient connections allowed beyond pool_size
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    """Generates thread-local database sessions for route dependencies."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()