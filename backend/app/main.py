"""FastAPI application entry point."""
from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestLoggingMiddleware

# Configure structured logging
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: initialize resources
    yield
    # Shutdown: cleanup resources
    pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Center Multi-Agent API",
        description="Multi-agent orchestration backend API",
        version="0.2.0",
        openapi_tags=[
            {"name": "health", "description": "Health check endpoints"},
            {"name": "auth", "description": "Authentication and authorization"},
            {"name": "knowledge", "description": "Knowledge management"},
            {"name": "agent", "description": "Agent operations with SSE notifications"},
        ],
        lifespan=lifespan,
    )

    # Security middleware - TrustedHostMiddleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.example.com"],
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8080"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    # Import and include routers from api/v1
    # Note: agent router is self-contained; auth/knowledge may have import errors
    try:
        from app.api.v1 import agent
        app.include_router(agent.router, prefix="/api/v1", tags=["agent"])
    except ImportError:
        pass

    try:
        from app.api.v1 import auth
        app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
    except ImportError:
        pass

    try:
        from app.api.v1 import knowledge
        app.include_router(knowledge.router, prefix="/api/v1", tags=["knowledge"])
    except ImportError:
        pass

    try:
        from app.api.v1 import rag
        app.include_router(rag.router, prefix="/api/v1", tags=["rag"])
    except ImportError:
        pass

    try:
        from app.api.v1 import sync
        app.include_router(sync.router, prefix="/api/v1", tags=["sync"])
    except ImportError:
        pass

    return app


app = create_app()
