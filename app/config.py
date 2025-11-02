# define global properties and configuration parameters
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')
    
    # Database Configuration
    # Option 1: Use full DATABASE_URL (takes precedence if provided)
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Option 2: Build from individual components (Supabase-friendly)
    if not DATABASE_URL:
        DB_TYPE = os.getenv('DB_TYPE', 'sqlite')  # 'sqlite' or 'postgresql'
        
        if DB_TYPE == 'postgresql':
            DB_HOST = os.getenv('DB_HOST', 'localhost')
            DB_PORT = os.getenv('DB_PORT', '5432')
            DB_USER = os.getenv('DB_USER', 'postgres')
            DB_PASSWORD = os.getenv('DB_PASSWORD', '')
            DB_NAME = os.getenv('DB_NAME', 'vendly')
            
            # Build PostgreSQL connection string
            DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        else:
            # Default to SQLite for local development
            DATABASE_URL = 'sqlite:///vendly.db'
    
    # JWT Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '15'))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '15'))