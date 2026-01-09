from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import asyncio
import time
from contextlib import asynccontextmanager

from .config import settings
from .database import create_tables
from .utils.logger import setup_logging, get_logger
from .utils.cache import cache
from .services.pipeline import recruiter_pipeline
from .routes.recruiter import router as recruiter_router
from .routes.auth import router as auth_router

# Setup logging
setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Starting Recruiter AI Platform")

    try:
        # Initialize database
        create_tables()
        logger.info("Database tables created/verified")

        # Initialize Redis cache
        await cache.connect()
        logger.info("Redis cache connected")

        # Initialize pipeline and agents
        await recruiter_pipeline.initialize()
        logger.info("AI pipeline initialized")

        logger.info("Recruiter AI Platform startup complete")

    except Exception as e:
        logger.error("Startup failed", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down Recruiter AI Platform")

    try:
        # Close connections
        await cache.disconnect()
        logger.info("Connections closed")

    except Exception as e:
        logger.error("Shutdown error", error=str(e))


# Create FastAPI app
app = FastAPI(
    title="Recruiter AI Platform",
    description="Production-grade multi-agent intelligence platform for recruiters",
    version=settings.app_version,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.api_host
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    start_time = time.time()

    # Get request details
    method = request.method
    url = str(request.url)
    client_ip = request.client.host if request.client else "unknown"

    logger.info(
        "HTTP request started",
        method=method,
        url=url,
        client_ip=client_ip
    )

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            "HTTP request completed",
            method=method,
            url=url,
            status_code=response.status_code,
            process_time=round(process_time, 3)
        )

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "HTTP request failed",
            method=method,
            url=url,
            error=str(e),
            process_time=round(process_time, 3)
        )
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        url=str(request.url),
        method=request.method,
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# Include routers
app.include_router(recruiter_router)
from .routes.auth import router as auth_router
app.include_router(auth_router)
app.include_router(auth_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Recruiter AI Platform",
        "version": settings.app_version,
        "description": "Multi-agent intelligence platform for recruiters",
        "docs": "/docs",
        "health": "/api/recruiter/health",
        "environment": settings.environment
    }


# Startup message
@app.on_event("startup")
async def startup_event():
    """Additional startup tasks."""
    logger.info(
        "Recruiter AI Platform ready",
        host=settings.api_host,
        port=settings.api_port,
        environment=settings.environment
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )
