# define global properties and configuration parameters
import os


class Config:
    DEBUG = True
    # TODO bout to change later on, when we implement postgres
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///vendly.db')