"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


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
        ],
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}

    # Import and include routers from api/v1 (auth, knowledge)
    # These modules are created in separate tasks
    try:
        from app.api.v1 import auth, knowledge

        app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
        app.include_router(knowledge.router, prefix="/api/v1", tags=["knowledge"])
    except ImportError:
        # Routers not yet implemented
        pass

    return app


app = create_app()
