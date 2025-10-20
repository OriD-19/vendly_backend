from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Any, Dict
from .config import Config

# Ensure DATABASE_URL is not None
if not Config.DATABASE_URL:
    raise ValueError("DATABASE_URL is not configured. Please set database environment variables.")

# Determine engine configuration based on database type
is_sqlite = Config.DATABASE_URL.startswith("sqlite")

# Engine configuration
engine_kwargs: Dict[str, Any] = {
    "echo": Config.DEBUG,
}

if is_sqlite:
    # SQLite-specific configuration
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL-specific configuration
    engine_kwargs["pool_pre_ping"] = True  # Verify connections before using
    engine_kwargs["pool_size"] = 10  # Connection pool size
    engine_kwargs["max_overflow"] = 20  # Max connections beyond pool_size
    engine_kwargs["pool_recycle"] = 3600  # Recycle connections after 1 hour

engine = create_engine(Config.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Database session dependency.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Creates all tables defined in models.
    """
    # Import all models here to ensure they're registered with Base
    from app.models import user, store, product, category, order, chat_message
    
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized: {Config.DATABASE_URL}")


def drop_all_tables():
    """
    Drop all database tables.
    WARNING: This will delete all data!
    Use only for testing/development.
    """
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped!")