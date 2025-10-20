"""
CORS Middleware Configuration for Vendly API
Handles Cross-Origin Resource Sharing.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI):
    """
    Configure CORS middleware for the application.
    
    Allows requests from specified origins (frontend apps).
    
    Args:
        app: FastAPI application instance
    """
    # Define allowed origins
    origins = [
        "http://localhost:3000",      # React/Next.js dev server
        "http://localhost:5173",      # Vite dev server
        "http://localhost:8000",      # API docs
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        # Add your production URLs here
        # "https://vendly.com",
        # "https://www.vendly.com",
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,           # Specific origins
        allow_credentials=True,          # Allow cookies
        allow_methods=["*"],             # Allow all HTTP methods
        allow_headers=["*"],             # Allow all headers
        expose_headers=["X-Process-Time", "X-Request-ID"],  # Custom headers
        max_age=600,                     # Cache preflight for 10 minutes
    )
