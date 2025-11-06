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
    origins = ["*"]  # Allow all origins
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,           # Allow all origins
        allow_credentials=True,          # Allow cookies
        allow_methods=["*"],             # Allow all HTTP methods
        allow_headers=["*"],             # Allow all headers
        expose_headers=["X-Process-Time", "X-Request-ID"],  # Custom headers
        max_age=600,                     # Cache preflight for 10 minutes
    )
