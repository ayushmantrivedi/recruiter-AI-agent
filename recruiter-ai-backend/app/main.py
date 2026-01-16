from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

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


def verify_database_schema():
    """Verify that critical database columns exist."""
    from .database import engine
    from sqlalchemy import inspect
    
    logger.info("Verifying database schema compliance...")
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('leads')]
    
    required_columns = ['role', 'location']
    missing = [col for col in required_columns if col not in columns]
    
    if missing:
        error_msg = f"CRITICAL DATABASE ERROR: Missing columns in 'leads' table: {missing}. Run migration script immediately."
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
        
    logger.info("Schema verification passed: All required columns present.")



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    logger.info("Starting Recruiter AI Platform")
    logger.info("Configuration loaded", database_url=settings.database.url, redis_url=settings.redis.url)

    try:
        # Initialize database
        from .database import test_db_connection
        if not test_db_connection():
            raise Exception("Database connection failed")
        create_tables()
        verify_database_schema()
        logger.info("Database tables created/verified")

        # Initialize Redis cache (optional)
        await cache.connect()
        if await cache.ping():
            logger.info("Redis cache connected")
        else:
            logger.warning("Redis cache not available, running without caching")

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

# Configure templates and static files
templates = Jinja2Templates(directory="app/ui/templates")
app.mount("/static", StaticFiles(directory="app/ui/static"), name="static")

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

# UI Routes
@app.get("/ui", response_class=HTMLResponse)
async def ui_home(request: Request):
    """Serve the main UI home page."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "version": settings.app_version
    })


@app.post("/ui/query")
async def ui_submit_query(
    request: Request,
    query: str = Form(...),
    recruiter_id: str = Form("")
):
    """Handle UI query submission."""
    try:
        # Create normalized query object directly
        from .routes.recruiter import NormalizedQuery, process_query_background
        from fastapi import BackgroundTasks

        # Validate input using the same normalization logic
        normalized_query = NormalizedQuery.from_dict({
            "query": query,
            "recruiter_id": recruiter_id or None
        })

        # Generate a unique query ID
        query_id = str(uuid.uuid4())

        # Import database session
        from .database import SessionLocal

        # For longer queries, insert into database immediately with processing status
        try:
            db = SessionLocal()
            # Insert new query record
            from .database import Query
            query_record = Query(
                id=query_id,
                recruiter_id=normalized_query.recruiter_id,
                query_text=normalized_query.query,
                processing_status="processing",
                created_at=datetime.utcnow()
            )
            db.add(query_record)
            db.commit()
            db.close()

            logger.info("UI job created and queued for processing",
                       query_id=query_id,
                       recruiter_id=normalized_query.recruiter_id,
                       query=normalized_query.query)

        except Exception as db_error:
            logger.error("UI failed to create job record",
                        error=str(db_error),
                        query_id=query_id,
                        recruiter_id=normalized_query.recruiter_id,
                        query=normalized_query.query)
            # Return error state for DB failure
            return templates.TemplateResponse("query_result.html", {
                "request": request,
                "query": {
                    "status": "failed",
                    "original_query": query,
                    "query_id": "error",
                    "error": f"Database error: {str(db_error)}"
                }
            })

        # Process in background with the generated query_id
        background_tasks = BackgroundTasks()
        background_tasks.add_task(
            process_query_background,
            query_id,
            normalized_query.query,
            normalized_query.recruiter_id
        )

        # Return processing status immediately
        return templates.TemplateResponse("query_result.html", {
            "request": request,
            "query": {
                "query_id": query_id,
                "status": "processing",
                "original_query": normalized_query.query,
                "leads": [],
                "total_leads_found": 0
            }
        })

    except Exception as e:
        logger.error("UI query submission failed", error=str(e))
        # Return error state
        return templates.TemplateResponse("query_result.html", {
            "request": request,
            "query": {
                "status": "failed",
                "original_query": query,
                "query_id": "error",
                "error": str(e)
            }
        })


@app.get("/ui/query/{query_id}")
async def ui_get_query_status(request: Request, query_id: str):
    """Get query status for UI polling."""
    try:
        # Import and call the actual API logic directly
        from .routes.recruiter import get_query_results

        result = await get_query_results(query_id)

        return templates.TemplateResponse("query_result.html", {
            "request": request,
            "query": result
        })

    except Exception as e:
        logger.error("UI query status check failed", error=str(e), query_id=query_id)
        # Return error state
        return templates.TemplateResponse("query_result.html", {
            "request": request,
            "query": {
                "status": "failed",
                "query_id": query_id,
                "error": f"Failed to check status: {str(e)}"
            }
        })


# Health endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from .database import test_db_connection
    from .utils.cache import cache

    db_status = "connected" if test_db_connection(max_retries=1) else "disconnected"
    redis_status = "connected" if await cache.ping() else "disconnected"

    status = "ok" if db_status == "connected" and redis_status == "connected" else "error"

    return {
        "status": status,
        "db": db_status,
        "redis": redis_status,
        "timestamp": datetime.utcnow().isoformat()
    }


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

    # Recover zombie jobs on startup
    await _recover_zombie_jobs()


async def _recover_zombie_jobs():
    """Recover jobs stuck in processing state."""
    from .database import SessionLocal, Query
    from datetime import datetime, timedelta
    import traceback

    logger.info("🔍 STARTING_ZOMBIE_JOB_RECOVERY")

    db_session = None
    try:
        db_session = SessionLocal()

        # Find jobs stuck in processing for more than 5 minutes
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        zombie_jobs = db_session.query(Query).filter(
            Query.processing_status == "processing",
            Query.created_at < five_minutes_ago
        ).all()

        recovered_count = 0
        for job in zombie_jobs:
            try:
                job.processing_status = "failed"
                job.execution_time = (datetime.utcnow() - job.created_at).total_seconds()
                logger.warning("♻️ ZOMBIE_JOB_RECOVERED",
                              query_id=job.id,
                              created_at=job.created_at.isoformat(),
                              stuck_duration_hours=((datetime.utcnow() - job.created_at).total_seconds() / 3600))
                recovered_count += 1
            except Exception as job_error:
                logger.error("❌ FAILED_TO_RECOVER_ZOMBIE_JOB",
                           query_id=job.id,
                           error=str(job_error))

        if recovered_count > 0:
            db_session.commit()
            logger.info("♻️ ZOMBIE_JOB_RECOVERY_COMPLETED",
                       recovered_count=recovered_count)
        else:
            logger.info("✅ NO_ZOMBIE_JOBS_FOUND")

        db_session.close()

    except Exception as e:
        logger.error("💥 ZOMBIE_JOB_RECOVERY_FAILED",
                    error=str(e),
                    traceback=traceback.format_exc())
        if db_session:
            try:
                db_session.close()
            except:
                pass


# Observability API endpoints
@app.get("/api/recruiter/jobs")
async def get_all_jobs(limit: int = 50, offset: int = 0):
    """Get all jobs with pagination."""
    from .database import SessionLocal, Query

    db_session = None
    try:
        db_session = SessionLocal()
        jobs = db_session.query(Query).order_by(Query.created_at.desc()).offset(offset).limit(limit).all()

        result = {
            "jobs": [
                {
                    "query_id": job.id,
                    "status": job.processing_status,
                    "query_text": job.query_text[:100] + "..." if len(job.query_text) > 100 else job.query_text,
                    "recruiter_id": job.recruiter_id,
                    "created_at": job.created_at.isoformat(),
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "execution_time": job.execution_time,
                    "total_cost": job.total_cost,
                    "leads_found": len(job.leads) if hasattr(job, 'leads') else 0
                }
                for job in jobs
            ],
            "total": len(jobs),
            "limit": limit,
            "offset": offset
        }
        db_session.close()
        return result

    except Exception as e:
        logger.error("❌ FAILED_TO_GET_JOBS", error=str(e))
        if db_session:
            try:
                db_session.close()
            except:
                pass
        raise HTTPException(status_code=500, detail="Failed to retrieve jobs")


@app.get("/api/recruiter/jobs/active")
async def get_active_jobs():
    """Get jobs currently in processing state."""
    from .database import SessionLocal, Query

    db_session = None
    try:
        db_session = SessionLocal()
        active_jobs = db_session.query(Query).filter(Query.processing_status == "processing").all()

        result = {
            "active_jobs": [
                {
                    "query_id": job.id,
                    "query_text": job.query_text[:100] + "..." if len(job.query_text) > 100 else job.query_text,
                    "recruiter_id": job.recruiter_id,
                    "created_at": job.created_at.isoformat(),
                    "processing_duration_seconds": (datetime.utcnow() - job.created_at).total_seconds()
                }
                for job in active_jobs
            ],
            "count": len(active_jobs)
        }
        db_session.close()
        return result

    except Exception as e:
        logger.error("❌ FAILED_TO_GET_ACTIVE_JOBS", error=str(e))
        if db_session:
            try:
                db_session.close()
            except:
                pass
        raise HTTPException(status_code=500, detail="Failed to retrieve active jobs")


@app.get("/api/recruiter/jobs/failed")
async def get_failed_jobs(limit: int = 20):
    """Get recently failed jobs."""
    from .database import SessionLocal, Query

    db_session = None
    try:
        db_session = SessionLocal()
        failed_jobs = db_session.query(Query).filter(
            Query.processing_status == "failed"
        ).order_by(Query.created_at.desc()).limit(limit).all()

        result = {
            "failed_jobs": [
                {
                    "query_id": job.id,
                    "query_text": job.query_text[:100] + "..." if len(job.query_text) > 100 else job.query_text,
                    "recruiter_id": job.recruiter_id,
                    "created_at": job.created_at.isoformat(),
                    "execution_time": job.execution_time
                }
                for job in failed_jobs
            ],
            "count": len(failed_jobs)
        }
        db_session.close()
        return result

    except Exception as e:
        logger.error("❌ FAILED_TO_GET_FAILED_JOBS", error=str(e))
        if db_session:
            try:
                db_session.close()
            except:
                pass
        raise HTTPException(status_code=500, detail="Failed to retrieve failed jobs")


@app.get("/api/recruiter/jobs/zombie")
async def get_zombie_jobs():
    """Get jobs that appear to be stuck (processing > 5 minutes)."""
    from .database import SessionLocal, Query
    from datetime import timedelta

    db_session = None
    try:
        db_session = SessionLocal()
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        zombie_jobs = db_session.query(Query).filter(
            Query.processing_status == "processing",
            Query.created_at < five_minutes_ago
        ).all()

        result = {
            "zombie_jobs": [
                {
                    "query_id": job.id,
                    "query_text": job.query_text[:100] + "..." if len(job.query_text) > 100 else job.query_text,
                    "recruiter_id": job.recruiter_id,
                    "created_at": job.created_at.isoformat(),
                    "stuck_duration_seconds": (datetime.utcnow() - job.created_at).total_seconds()
                }
                for job in zombie_jobs
            ],
            "count": len(zombie_jobs)
        }
        db_session.close()
        return result

    except Exception as e:
        logger.error("❌ FAILED_TO_GET_ZOMBIE_JOBS", error=str(e))
        if db_session:
            try:
                db_session.close()
            except:
                pass
        raise HTTPException(status_code=500, detail="Failed to retrieve zombie jobs")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info"
    )
