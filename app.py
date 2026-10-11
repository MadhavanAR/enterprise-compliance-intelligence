"""
Main application entry point for Enterprise Compliance Intelligence.
Exports the FastAPI application instance for Uvicorn / Gunicorn deployment.
"""

from api.main import app

__all__ = ["app"]
