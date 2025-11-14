"""Main FastAPI application."""

import logging

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import Response
from fastapi.responses import JSONResponse
from typing import Callable, cast
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.routers import api
from app.utils.web3_client import web3_client
from app.settings import settings

# Configure stdlib logging so INFO logs surface before structlog wraps them
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting application", app_name="Blockchain Banking API")

    # Connect to blockchain
    connected = await web3_client.connect()
    if not connected:
        logger.error("Failed to connect to blockchain")

    yield

    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title="Blockchain Banking API",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Add rate limiting
app.state.limiter = limiter


def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Proxy handler to satisfy typing for SlowAPI rate limit errors."""

    return _rate_limit_exceeded_handler(request, exc)


app.add_exception_handler(
    RateLimitExceeded,
    cast("Callable[[Request, Exception], Response]", rate_limit_handler),
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    logger.info(
        "HTTP request",
        method=request.method,
        url=str(request.url),
        client=request.client.host if request.client else None,
    )

    response = await call_next(request)

    logger.info(
        "HTTP response",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
    )

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception",
        method=request.method,
        url=str(request.url),
        error=str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error": str(exc)},
    )


# Include routers
app.include_router(api.router, prefix="/api")


@app.get("/", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
