"""
Database initialization script.

This script creates all database tables based on your SQLAlchemy models.
Run this after setting up your PostgreSQL database in Supabase.

Usage:
    python init_db.py
"""

from app.database import init_db, engine
from app.config import Config
from sqlalchemy import text


def check_connection():
    """Test database connection."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def main():
    """Initialize the database."""
    print("=" * 60)
    print("Vendly Database Initialization")
    print("=" * 60)
    print(f"\nDatabase URL: {Config.DATABASE_URL}")
    db_type = Config.DB_TYPE if hasattr(Config, 'DB_TYPE') else 'sqlite'
    print(f"Database Type: {db_type}")
    print()
    
    # Check connection
    if not check_connection():
        print("\n⚠️  Please check your database configuration and try again.")
        return
    
    # Initialize database
    print("\n📦 Creating database tables...")
    try:
        init_db()
        print("✅ All tables created successfully!")
        print()
        print("Tables created:")
        print("  - users")
        print("  - user_preferences")
        print("  - stores")
        print("  - categories")
        print("  - products")
        print("  - product_images")
        print("  - tags")
        print("  - product_tags")
        print("  - orders")
        print("  - order_products")
        print("  - chat_messages")
        print()
        print("✨ Database is ready to use!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
