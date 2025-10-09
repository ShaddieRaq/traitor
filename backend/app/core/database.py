from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Enhanced SQLite configuration for concurrent access
sqlite_connect_args = {
    "check_same_thread": False,
    "timeout": 30,  # 30 second timeout for database locks
    "isolation_level": None,  # Enable autocommit mode for better concurrency
}

engine = create_engine(
    settings.database_url,
    connect_args=sqlite_connect_args if "sqlite" in settings.database_url else {},
    pool_timeout=30,  # Connection pool timeout
    pool_recycle=3600,  # Recycle connections every hour
    echo=False  # Disable SQL logging for performance
)

# Configure SQLite for better concurrency
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better concurrency and performance."""
    if "sqlite" in settings.database_url:
        cursor = dbapi_connection.cursor()
        try:
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Set busy timeout to 30 seconds
            cursor.execute("PRAGMA busy_timeout=30000")
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys=ON")
            # Optimize performance
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            logger.info("✅ SQLite WAL mode and concurrency settings applied")
        except Exception as e:
            logger.error(f"❌ Failed to set SQLite pragmas: {e}")
        finally:
            cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
