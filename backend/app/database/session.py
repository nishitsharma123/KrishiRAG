import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings
from backend.app.core.logging import logger

# Ensure directory for sqlite file exists
if settings.DATABASE_URL.startswith("sqlite"):
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True
)

# Enable SQLite WAL (Write-Ahead Logging) mode and foreign keys for high concurrency
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from backend.app.models import document, conversation, message, feedback # noqa
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
