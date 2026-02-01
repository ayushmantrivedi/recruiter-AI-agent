from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import uuid
from ..services.pipeline import recruiter_pipeline
from ..database import get_db, SessionLocal, Query
from ..config import settings
from ..utils.logger import get_logger
from .auth import get_current_user, Recruiter

logger = get_logger("recruiter_routes")

router = APIRouter(prefix="/api/recruiter", tags=["recruiter"])


# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for recruiter query."""
    query: str = Field(..., description="Recruiter search query", min_length=3, max_length=500)
    recruiter_id: Optional[str] = Field(None, description="Optional recruiter identifier")


class NormalizedQuery:
    """Normalized internal query object for pipeline consistency."""
    def __init__(self, query: str, recruiter_id: Optional[str] = None):
        self.query = query
        self.recruiter_id = recruiter_id

    @classmethod
    def from_dict(cls, data: dict) -> "NormalizedQuery":
        """Create from dictionary input."""
        query = data.get("query")
        recruiter_id = data.get("recruiter_id")

        if not query:
            raise ValueError("query field is required")
        if len(query.strip()) < 3:
            raise ValueError("query must be at least 3 characters")
        if len(query.strip()) > 500:
            raise ValueError("query must be at most 500 characters")

        return cls(query=query.strip(), recruiter_id=recruiter_id)

    @classmethod
    def from_request(cls, request: QueryRequest) -> "NormalizedQuery":
        """Create from Pydantic request model."""
        return cls(query=request.query, recruiter_id=request.recruiter_id)

    def to_dict(self) -> dict:
        """Convert to dictionary for backward compatibility."""
        return {
            "query": self.query,
            "recruiter_id": self.recruiter_id
        }


async def parse_query_input(request: Request) -> NormalizedQuery:
    """Parse query input from either JSON or form-encoded data."""
    content_type = request.headers.get("content-type", "").lower()

    try:
        if "application/json" in content_type:
            # Parse JSON input
            data = await request.json()
            logger.info("Parsed JSON input", content_type=content_type)
        elif "application/x-www-form-urlencoded" in content_type:
            # Parse form input
            form_data = await request.form()
            data = {
                "query": form_data.get("query"),
                "recruiter_id": form_data.get("recruiter_id")
            }
            logger.info("Parsed form input", content_type=content_type)
        else:
            # Try JSON first, fallback to form
            try:
                data = await request.json()
                logger.info("Parsed fallback JSON input", content_type=content_type)
            except Exception:
                form_data = await request.form()
                data = {
                    "query": form_data.get("query"),
                    "recruiter_id": form_data.get("recruiter_id")
                }
                logger.info("Parsed fallback form input", content_type=content_type)

        # Validate and normalize
        normalized = NormalizedQuery.from_dict(data)
        logger.info("Input normalized successfully",
                   query_length=len(normalized.query),
                   has_recruiter_id=normalized.recruiter_id is not None)

        return normalized

    except ValueError as e:
        logger.error("Input validation failed", error=str(e), content_type=content_type)
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        logger.error("Input parsing failed", error=str(e), content_type=content_type)
        raise HTTPException(status_code=400, detail="Invalid request format. Expected JSON or form data.")



class IntelligenceMetadata(BaseModel):
    """Structured metadata extracted from query."""
    intent: str
    role: str
    skills: List[str]
    experience: int
    seniority: str
    location: str

class IntelligenceSignals(BaseModel):
    """Numeric intelligence metrics."""
    hiring_pressure: float
    role_scarcity: float
    outsourcing_likelihood: float
    market_difficulty: float


# Import Synthesis Agent
from ..agents.synthesis_agent import synthesis_agent

class QueryResponse(BaseModel):
    """Response model for query processing."""
    query_id: str
    status: str
    original_query: str
    processing_time: Optional[float] = None
    
    # New Standard Fields
    intelligence: Optional[IntelligenceMetadata] = None
    signals: Optional[IntelligenceSignals] = None
    
    # Synthesis Field (New)
    synthesis_report: Optional[str] = None
    
    # Legacy / Optional
    concept_vector: Optional[Dict[str, Any]] = None # Relaxed type for backward compat
    
    constraints: Optional[Dict[str, Any]] = None
    orchestration_summary: Optional[Dict[str, Any]] = None
    leads: List[Dict[str, Any]] = []
    total_leads_found: int = 0
    completed_at: Optional[str] = None
    error: Optional[str] = None

# ... (LeadResponse, etc remain same)

@router.get("/query/{query_id}", response_model=QueryResponse)
async def get_query_results(query_id: str, current_user: Recruiter = Depends(get_current_user)):
    """Get the results of a processed query.

    Returns the complete results once processing is finished,
    or current status if still processing.
    """
    try:
        logger.info("Getting query status", query_id=query_id, identity=current_user.email)
        result = await recruiter_pipeline.get_query_status(query_id)
        
        if result and result.get('recruiter_id') != current_user.email:
            logger.warning("Unauthorized query access attempt", query_id=query_id, identity=current_user.email)
            raise HTTPException(status_code=403, detail="Unauthorized access to this query")

        logger.info("Pipeline result", query_id=query_id, result=result)

        if not result:
            logger.error("Query not found in pipeline", query_id=query_id)
            raise HTTPException(status_code=404, detail="Query not found")
            
        # Synthesis report is now pre-generated by the pipeline
        # and retrieved from the database/cache automatically.

        return QueryResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Query results retrieval failed", error=str(e), query_id=query_id)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve query results: {str(e)}")


class LeadResponse(BaseModel):
    """Response model for individual leads."""
    company: str
    score: float
    confidence: float
    reasons: List[str]
    evidence_count: int
    last_updated: str


class QueryStatusResponse(BaseModel):
    """Response model for query status."""
    query_id: str
    status: str  # pending, processing, completed, failed
    progress: Optional[float] = None  # 0.0 to 1.0
    estimated_completion: Optional[str] = None


class RecruiterStatsResponse(BaseModel):
    """Response model for recruiter statistics."""
    recruiter_id: str
    total_queries: int
    total_leads: int
    average_lead_score: float
    total_cost: float
    leads_per_query: float


@router.post("/query", response_model=QueryResponse)
async def process_recruiter_query(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Recruiter = Depends(get_current_user),
    db=Depends(get_db)
):
    """Process a recruiter search query through the AI agent pipeline.

    This endpoint accepts a recruiter's search intent and processes it through:
    1. Concept Reasoner (extracts hiring concepts and constraints)
    2. Action Orchestrator (gathers evidence from multiple APIs)
    3. Signal Judge (scores and ranks company leads)

    Supports both JSON and form-encoded input for compatibility with different clients.

    Returns immediately with query ID for status polling, or complete results if fast.
    """
    try:
        # Parse and validate input from either JSON or form data
        normalized_query = await parse_query_input(request)

        # Generate a unique query ID
        query_id = str(uuid.uuid4())
        
        # Override recruiter_id from authenticated user
        user_identity = current_user.email

        # For very short queries, process synchronously
        if len(normalized_query.query.split()) <= 3:
            result = await recruiter_pipeline.process_recruiter_query(
                normalized_query.query,
                user_identity,
                query_id=query_id  # Pass the query_id
            )
            return QueryResponse(**result)

        # For longer queries, insert into database immediately with processing status
        try:
            # Insert new query record
            query_record = Query(
                id=query_id,
                recruiter_id=user_identity,
                query_text=normalized_query.query,
                processing_status="processing",
                created_at=datetime.utcnow()
            )
            db.add(query_record)
            db.commit()

            logger.info("Job created and queued for processing",
                       query_id=query_id,
                       recruiter_id=user_identity,
                       query=normalized_query.query)

        except Exception as db_error:
            logger.error("Failed to create job record",
                        error=str(db_error),
                        query_id=query_id,
                        recruiter_id=normalized_query.recruiter_id,
                        query=normalized_query.query)
            raise HTTPException(status_code=500, detail="Failed to queue job")

        # Process in background with the generated query_id
        background_tasks.add_task(
            process_query_background,
            query_id,
            normalized_query.query,
            user_identity
        )

        # Return processing status with real query ID
        return QueryResponse(
            query_id=query_id,
            status="processing",
            original_query=normalized_query.query,
            leads=[],
            total_leads_found=0
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("Query processing failed",
                    error=str(e),
                    query=getattr(normalized_query, 'query', 'unknown') if 'normalized_query' in locals() else 'unknown')
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


async def process_query_background(query_id: str, query: str, recruiter_id: str = None):
    """Background task to process recruiter queries with comprehensive error handling and timeouts."""
    import asyncio
    import traceback

    # Job lifecycle constants
    JOB_TIMEOUT_SECONDS = 300  # 5 minutes max per job
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 2  # seconds

    logger.info("🔄 JOB_CREATED", query_id=query_id, query=query, recruiter_id=recruiter_id)

    # Update job status to processing (double-check)
    db_session = None
    try:
        db_session = SessionLocal()
        query_record = db_session.query(Query).filter(Query.id == query_id).first()
        if query_record and query_record.processing_status == "pending":
            query_record.processing_status = "processing"
            db_session.commit()
            logger.info("📝 JOB_STATUS_UPDATED_TO_PROCESSING", query_id=query_id)
        elif query_record:
            logger.warning("⚠️ JOB_ALREADY_IN_PROCESSING", query_id=query_id, status=query_record.processing_status)
        db_session.close()
        db_session = None
    except Exception as db_error:
        logger.error("❌ FAILED_TO_UPDATE_JOB_STATUS",
                    error=str(db_error),
                    query_id=query_id,
                    traceback=traceback.format_exc())
        if db_session:
            try:
                db_session.close()
            except:
                pass
        return

    # Execute job with timeout and retry logic
    for attempt in range(MAX_RETRIES):
        try:
            logger.info("🚀 JOB_STARTED",
                       query_id=query_id,
                       attempt=attempt + 1,
                       max_attempts=MAX_RETRIES)

            # Execute pipeline with timeout - UNIFIED PATH
            # Uses the same RecruiterPipeline.process_recruiter_query as sync path
            # This ensures ExecutionReport is always created and persisted
            await asyncio.wait_for(
                recruiter_pipeline.process_recruiter_query(
                    query,
                    recruiter_id,
                    query_id=query_id
                ),
                timeout=JOB_TIMEOUT_SECONDS
            )

            logger.info("✅ JOB_COMPLETED_SUCCESSFULLY", query_id=query_id, attempt=attempt + 1)
            return

        except asyncio.TimeoutError:
            logger.error("⏰ JOB_TIMEOUT_EXCEEDED",
                        query_id=query_id,
                        attempt=attempt + 1,
                        timeout_seconds=JOB_TIMEOUT_SECONDS)

            # Mark as failed due to timeout
            _mark_job_failed(query_id, f"Job timed out after {JOB_TIMEOUT_SECONDS} seconds")

            # Don't retry timeouts
            return

        except Exception as e:
            # DEBUG: Write full error to file
            with open("logs/debug_error.log", "a") as f:
                f.write(f"\n--- ERROR Query {query_id} Attempt {attempt+1} ---\n")
                f.write(traceback.format_exc())
                
            logger.error("💥 JOB_EXECUTION_FAILED",
                        error=str(e),
                        query_id=query_id,
                        attempt=attempt + 1,
                        traceback=traceback.format_exc())

            # On final attempt, mark as failed
            if attempt == MAX_RETRIES - 1:
                _mark_job_failed(query_id, f"Job failed after {MAX_RETRIES} attempts: {str(e)}")
                logger.error("❌ JOB_FAILED_PERMANENTLY",
                           query_id=query_id,
                           final_error=str(e))
                return

            # Exponential backoff for retries
            retry_delay = RETRY_DELAY_BASE * (2 ** attempt)
            logger.info("🔄 JOB_RETRY_SCHEDULED",
                       query_id=query_id,
                       attempt=attempt + 1,
                       delay_seconds=retry_delay)

            await asyncio.sleep(retry_delay)


# REMOVED: _execute_pipeline_with_checkpoint (Split-brain source)
# The async path now uses RecruiterPipeline.process_recruiter_query directly.
# This ensures a single, deterministic execution path with full ExecutionReport support.


def _mark_job_failed(query_id: str, error_message: str):
    """Mark job as failed in database."""
    import traceback

    db_session = None
    try:
        db_session = SessionLocal()
        query_record = db_session.query(Query).filter(Query.id == query_id).first()
        if query_record:
            query_record.processing_status = "failed"
            query_record.execution_time = 0  # Could track failed time separately
            db_session.commit()
            logger.info("❌ JOB_MARKED_AS_FAILED", query_id=query_id, error=error_message)
        else:
            logger.error("❓ JOB_RECORD_NOT_FOUND_FOR_FAILURE_UPDATE", query_id=query_id)
        db_session.close()
    except Exception as db_error:
        logger.error("💥 FAILED_TO_MARK_JOB_AS_FAILED",
                    error=str(db_error),
                    query_id=query_id,
                    original_error=error_message,
                    traceback=traceback.format_exc())
        if db_session:
            try:
                db_session.close()
            except:
                pass





@router.get("/stats/{recruiter_id}", response_model=RecruiterStatsResponse)
async def get_recruiter_stats(recruiter_id: str, current_user: Recruiter = Depends(get_current_user)):
    """Get statistics for a specific recruiter.
    This endpoint provides summary metrics including total runs,
    leads generated, and cost analysis for the authenticated identity.
    """
    try:
        # Use current_user identity string instead of integer ID
        stats = await recruiter_pipeline.get_recruiter_stats(current_user.email)
        return stats
    except Exception as e:
        logger.error("Failed to retrieve recruiter stats", error=str(e), identity=current_user.email)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leads")
async def get_leads(limit: int = 50, offset: int = 0, current_user: Recruiter = Depends(get_current_user), db=Depends(get_db)):
    """Get leads for the authenticated recruiter."""
    user_identity = current_user.email
    try:
        from ..database import Lead
        query = db.query(Lead).join(Query).filter(Query.recruiter_id == user_identity)

        leads = query.offset(offset).limit(limit).all()

        return {
            "leads": [
                {
                    "id": lead.id,
                    "company": lead.company_name,
                    "score": lead.score,
                    "confidence": lead.confidence,
                    "reasons": lead.reasons,
                    # evidence_count removed - not in DB schema
                    "created_at": lead.created_at.isoformat(),
                    "query_id": lead.query_id
                }
                for lead in leads
            ],
            "total": len(leads)
        }

    except Exception as e:
        logger.error("Leads retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve leads: {str(e)}")


@router.get("/leads/{lead_id}")
async def get_lead_by_id(lead_id: int, db=Depends(get_db)):
    """Get a specific lead by ID."""
    try:
        from ..database import Lead
        lead = db.query(Lead).filter(Lead.id == lead_id).first()

        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
            
        # Check permissions
        parent_query = db.query(Query).filter(Query.id == lead.query_id).first()
        if not parent_query or parent_query.recruiter_id != str(current_user.id):
             raise HTTPException(status_code=403, detail="Unauthorized access to this lead")

        return {
            "id": lead.id,
            "company": lead.company_name,
            "score": lead.score,
            "confidence": lead.confidence,
            "reasons": lead.reasons,
            # evidence_count removed - not in DB schema
            "evidence_objects": lead.evidence_objects,
            "job_postings": lead.job_postings,
            "news_mentions": lead.news_mentions,
            "created_at": lead.created_at.isoformat(),
            "query_id": lead.query_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Lead retrieval failed", error=str(e), lead_id=lead_id)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve lead: {str(e)}")


@router.get("/queries")
async def get_queries(limit: int = 20, offset: int = 0, current_user: Recruiter = Depends(get_current_user), db=Depends(get_db)):
    """Get query history for the authenticated recruiter."""
    user_identity = current_user.email
    try:
        query = db.query(Query).filter(Query.recruiter_id == user_identity)

        queries = query.offset(offset).limit(limit).all()

        return {
            "queries": [
                {
                    "id": q.id,
                    "query_text": q.query_text,
                    "status": q.processing_status,
                    "confidence_score": q.confidence_score,
                    "total_cost": q.total_cost,
                    "execution_time": q.execution_time,
                    "created_at": q.created_at.isoformat(),
                    "completed_at": q.completed_at.isoformat() if q.completed_at else None
                }
                for q in queries
            ],
            "total": len(queries)
        }

    except Exception as e:
        logger.error("Queries retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve queries: {str(e)}")


@router.get("/metrics/dashboard")
async def get_dashboard_metrics(current_user: Recruiter = Depends(get_current_user), db=Depends(get_db)):
    """Get dashboard metrics for the authenticated recruiter."""
    user_identity = current_user.email
    try:
        from ..database import Lead, Query
        from sqlalchemy import func

        # Filter by authenticated user's queries
        user_queries = db.query(Query.id).filter(Query.recruiter_id == user_identity)
        user_query_ids = [q[0] for q in user_queries.all()]

        # Today's leads
        today = datetime.utcnow().date()
        today_leads = db.query(func.count(Lead.id)).filter(
            Lead.query_id.in_(user_query_ids),
            func.date(Lead.created_at) == today
        ).scalar() or 0

        # Total leads
        total_leads = db.query(func.count(Lead.id)).filter(
            Lead.query_id.in_(user_query_ids)
        ).scalar() or 0

        # Average score
        avg_score = db.query(func.avg(Lead.score)).filter(
            Lead.query_id.in_(user_query_ids)
        ).scalar() or 0.0

        # Recent queries
        recent_queries = db.query(Query).filter(
            Query.recruiter_id == user_identity
        ).order_by(Query.created_at.desc()).limit(5).all()

        # Top companies by leads
        top_companies = db.query(
            Lead.company_name,
            func.count(Lead.id).label('count')
        ).join(Query).filter(
            Query.recruiter_id == user_identity
        ).group_by(Lead.company_name).order_by(func.count(Lead.id).desc()).limit(5).all()

        return {
            "today_leads": today_leads,
            "total_leads": total_leads,
            "average_score": round(float(avg_score), 2),
            "recent_queries": [
                {
                    "id": q.id,
                    "query_text": q.query_text[:50] + "..." if len(q.query_text) > 50 else q.query_text,
                    "status": q.processing_status,
                    "created_at": q.created_at.isoformat()
                }
                for q in recent_queries
            ],
            "top_companies": [
                {"company": company, "leads": count}
                for company, count in top_companies
            ]
        }

    except Exception as e:
        logger.error("Dashboard metrics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dashboard metrics: {str(e)}")


@router.get("/metrics/usage")
async def get_usage_metrics(period: str = "30d", current_user: Recruiter = Depends(get_current_user), db=Depends(get_db)):
    """Get usage metrics for the authenticated recruiter."""
    user_identity = current_user.email
    try:
        from ..database import Query, Lead
        from sqlalchemy import func

        # Parse period
        days = int(period.rstrip('d'))

        # Date filter
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Usage stats
        total_queries = db.query(func.count(Query.id)).filter(
            Query.recruiter_id == user_identity,
            Query.created_at >= cutoff_date
        ).scalar() or 0

        total_cost = db.query(func.sum(Query.total_cost)).filter(
            Query.recruiter_id == user_identity,
            Query.created_at >= cutoff_date
        ).scalar() or 0.0

        successful_queries = db.query(func.count(Query.id)).filter(
            Query.recruiter_id == user_identity,
            Query.created_at >= cutoff_date,
            Query.processing_status == "completed"
        ).scalar() or 0

        return {
            "period": period,
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "success_rate": round((successful_queries / total_queries * 100) if total_queries > 0 else 0, 2),
            "total_cost": round(float(total_cost), 2),
            "average_cost_per_query": round((total_cost / total_queries) if total_queries > 0 else 0, 2)
        }

    except Exception as e:
        logger.error("Usage metrics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve usage metrics: {str(e)}")


@router.get("/metrics/performance")
async def get_performance_metrics(current_user: Recruiter = Depends(get_current_user), db=Depends(get_db)):
    """Get performance metrics for the authenticated recruiter."""
    user_identity = current_user.email
    try:
        from ..database import Query, Lead
        from sqlalchemy import func

        # Average execution time
        avg_execution_time = db.query(func.avg(Query.execution_time)).filter(
            Query.recruiter_id == user_identity
        ).scalar() or 0.0

        # Average lead score
        avg_lead_score = db.query(func.avg(Lead.score)).join(Query).filter(
            Query.recruiter_id == user_identity
        ).scalar() or 0.0

        # Query success rate
        total_queries = db.query(func.count(Query.id)).filter(
            Query.recruiter_id == user_identity
        ).scalar() or 0
        successful_queries = db.query(func.count(Query.id)).filter(
            Query.recruiter_id == user_identity,
            Query.processing_status == "completed"
        ).scalar() or 0

        success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0

        # Leads per query
        total_leads = db.query(func.count(Lead.id)).join(Query).filter(
            Query.recruiter_id == user_identity
        ).scalar() or 0
        avg_leads_per_query = (total_leads / total_queries) if total_queries > 0 else 0

        return {
            "average_execution_time": round(float(avg_execution_time), 2),
            "average_lead_score": round(float(avg_lead_score), 2),
            "query_success_rate": round(success_rate, 2),
            "average_leads_per_query": round(avg_leads_per_query, 2),
            "total_queries": total_queries,
            "total_leads": total_leads
        }

    except Exception as e:
        logger.error("Performance metrics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve performance metrics: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "environment": settings.environment
    }


@router.get("/metrics")
async def get_metrics():
    """Get system metrics for monitoring and observability."""
    try:
        # This would integrate with Prometheus metrics in production
        return {
            "total_queries_processed": 0,  # Would be from metrics
            "active_queries": 0,
            "average_processing_time": 0.0,
            "total_cost_incurred": 0.0,
            "cache_hit_rate": 0.0,
            "api_error_rate": 0.0,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Metrics retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")


@router.post("/feedback")
async def submit_feedback(feedback: Dict[str, Any]):
    """Submit feedback on leads for learning improvement.

    Allows recruiters to provide feedback on lead quality,
    which is used to improve future recommendations.
    """
    try:
        # Validate feedback structure
        required_fields = ["query_id", "company", "rating", "feedback_type"]
        for field in required_fields:
            if field not in feedback:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )

        # In production, this would save to database and trigger learning
        logger.info("Feedback submitted",
                   query_id=feedback.get("query_id"),
                   company=feedback.get("company"),
                   rating=feedback.get("rating"))

        return {
            "status": "feedback_received",
            "message": "Thank you for your feedback. This will help improve future recommendations."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Feedback submission failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")


# Admin endpoints (would be protected in production)
@router.get("/admin/queries", response_model=List[Dict[str, Any]])
async def get_all_queries(limit: int = 50, offset: int = 0):
    """Admin endpoint to get all queries (for debugging/monitoring)."""
    try:
        # This would be properly secured and paginated in production
        return []

    except Exception as e:
        logger.error("Admin queries retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve queries: {str(e)}")


@router.delete("/admin/cache")
async def clear_cache():
    """Admin endpoint to clear system cache."""
    try:
        # This would clear Redis cache in production
        logger.info("Cache cleared by admin")
        return {"status": "cache_cleared"}

    except Exception as e:
        logger.error("Cache clearing failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
