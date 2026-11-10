import os
from sqlalchemy import create_engine, event, text
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

    # Lightweight migration for SQLite: Ensure new columns exist on existing tables
    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            try:
                table_info = conn.execute(text("PRAGMA table_info(documents)")).fetchall()
                existing_cols = {row[1] for row in table_info}

                col_defs = [
                    ("file_hash", "VARCHAR(64)"),
                    ("file_size", "INTEGER DEFAULT 0"),
                    ("mime_type", "VARCHAR(64)"),
                    ("chunk_count", "INTEGER DEFAULT 0"),
                    ("error_message", "TEXT")
                ]

                for col_name, col_type in col_defs:
                    if col_name not in existing_cols:
                        logger.info(f"Applying schema migration: ALTER TABLE documents ADD COLUMN {col_name} {col_type}")
                        conn.execute(text(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception as e:
                logger.warning(f"Schema check error: {e}")

    logger.info("Database tables initialized successfully.")
