# define global properties and configuration parameters
import os


class Config:
    DEBUG = True
    # TODO bout to change later on, when we implement postgres
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///vendly.db')
    
    # JWT Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15 minutes
    REFRESH_TOKEN_EXPIRE_DAYS = 15  # 15 days