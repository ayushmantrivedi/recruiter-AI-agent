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


class QueryResponse(BaseModel):
    """Response model for query processing."""
    query_id: str
    status: str
    original_query: str
    processing_time: Optional[float] = None
    concept_vector: Optional[Dict[str, float]] = None
    constraints: Optional[Dict[str, Any]] = None
    orchestration_summary: Optional[Dict[str, Any]] = None
    leads: List[Dict[str, Any]] = []
    total_leads_found: int = 0
    completed_at: Optional[str] = None
    error: Optional[str] = None


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

        # For very short queries, process synchronously
        if len(normalized_query.query.split()) <= 3:
            result = await recruiter_pipeline.process_recruiter_query(
                normalized_query.query,
                normalized_query.recruiter_id,
                query_id=query_id  # Pass the query_id
            )
            return QueryResponse(**result)

        # For longer queries, insert into database immediately with processing status
        try:
            # Insert new query record
            query_record = Query(
                id=query_id,
                recruiter_id=normalized_query.recruiter_id,
                query_text=normalized_query.query,
                processing_status="processing",
                created_at=datetime.utcnow()
            )
            db.add(query_record)
            db.commit()

            logger.info("Job created and queued for processing",
                       query_id=query_id,
                       recruiter_id=normalized_query.recruiter_id,
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
            normalized_query.recruiter_id
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

            # Execute pipeline with timeout
            await asyncio.wait_for(
                _execute_pipeline_with_checkpoint(query_id, query, recruiter_id),
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


async def _execute_pipeline_with_checkpoint(query_id: str, query: str, recruiter_id: str = None):
    """Execute pipeline with detailed checkpoints."""
    import traceback

    logger.info("🔍 PIPELINE_STARTED", query_id=query_id)

    try:
        # Step 1: Concept Reasoning
        logger.info("🧠 STEP_1_CONCEPT_REASONING_STARTED", query_id=query_id)
        concept_result = await recruiter_pipeline.concept_reasoner.process_query(query, recruiter_id)
        logger.info("🧠 STEP_1_CONCEPT_REASONING_COMPLETED",
                   query_id=query_id,
                   concept_vector_length=len(concept_result.get("concept_vector", {})))

        # Step 2: Action Orchestration
        logger.info("🎯 STEP_2_ACTION_ORCHESTRATION_STARTED", query_id=query_id)
        orchestration_result = await recruiter_pipeline.action_orchestrator.orchestrate_search(
            query_id,
            concept_result["concept_vector"],
            concept_result["constraints"]
        )
        logger.info("🎯 STEP_2_ACTION_ORCHESTRATION_COMPLETED",
                   query_id=query_id,
                   total_steps=orchestration_result.get("total_steps", 0),
                   total_cost=orchestration_result.get("total_cost", 0))

        # Step 3: Signal Judgment
        logger.info("⚖️ STEP_3_SIGNAL_JUDGMENT_STARTED", query_id=query_id)
        leads = await recruiter_pipeline.signal_judge.judge_leads(
            query_id,
            orchestration_result["evidence_objects"],
            concept_result["constraints"]
        )
        logger.info("⚖️ STEP_3_SIGNAL_JUDGMENT_COMPLETED",
                   query_id=query_id,
                   leads_found=len(leads))

        # Step 4: Database Save
        logger.info("💾 STEP_4_DATABASE_SAVE_STARTED", query_id=query_id)
        await recruiter_pipeline._save_to_database({
            "query_id": query_id,
            "recruiter_id": recruiter_id,
            "original_query": query,
            "processing_time": 0,  # Will be updated by pipeline
            "concept_vector": concept_result["concept_vector"],
            "constraints": concept_result["constraints"],
            "orchestration_summary": {
                "confidence": orchestration_result["confidence"],
                "total_steps": orchestration_result["total_steps"],
                "total_cost": orchestration_result["total_cost"],
                "evidence_count": len(orchestration_result["evidence_objects"])
            },
            "leads": leads[:20],  # Limit to top 20 leads
            "total_leads_found": len(leads),
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat()
        })
        logger.info("💾 STEP_4_DATABASE_SAVE_COMPLETED", query_id=query_id)

        logger.info("🎉 PIPELINE_COMPLETED_SUCCESSFULLY", query_id=query_id)

    except Exception as e:
        logger.error("💥 PIPELINE_EXECUTION_FAILED",
                    error=str(e),
                    query_id=query_id,
                    traceback=traceback.format_exc())
        raise


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


@router.get("/query/{query_id}", response_model=QueryResponse)
async def get_query_results(query_id: str):
    """Get the results of a processed query.

    Returns the complete results once processing is finished,
    or current status if still processing.
    """
    try:
        logger.info("Getting query status", query_id=query_id)
        result = await recruiter_pipeline.get_query_status(query_id)
        logger.info("Pipeline result", query_id=query_id, result=result)

        if not result:
            logger.error("Query not found in pipeline", query_id=query_id)
            raise HTTPException(status_code=404, detail="Query not found")

        return QueryResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Query results retrieval failed", error=str(e), query_id=query_id)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve query results: {str(e)}")


@router.get("/stats/{recruiter_id}", response_model=RecruiterStatsResponse)
async def get_recruiter_stats(recruiter_id: str):
    """Get statistics for a specific recruiter.

    Returns aggregated statistics about queries, leads, costs, and performance.
    """
    try:
        stats = await recruiter_pipeline.get_recruiter_stats(recruiter_id)
        return RecruiterStatsResponse(**stats)

    except Exception as e:
        logger.error("Recruiter stats retrieval failed", error=str(e), recruiter_id=recruiter_id)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recruiter stats: {str(e)}")


@router.get("/leads")
async def get_leads(recruiter_id: str = None, limit: int = 50, offset: int = 0, db=Depends(get_db)):
    """Get leads for a recruiter."""
    try:
        from ..database import Lead
        query = db.query(Lead)
        if recruiter_id:
            query = query.join(Query).filter(Query.recruiter_id == recruiter_id)

        leads = query.offset(offset).limit(limit).all()

        return {
            "leads": [
                {
                    "id": lead.id,
                    "company": lead.company_name,
                    "score": lead.score,
                    "confidence": lead.confidence,
                    "reasons": lead.reasons,
                    "evidence_count": lead.evidence_count,
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

        return {
            "id": lead.id,
            "company": lead.company_name,
            "score": lead.score,
            "confidence": lead.confidence,
            "reasons": lead.reasons,
            "evidence_count": lead.evidence_count,
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
async def get_queries(recruiter_id: str = None, limit: int = 20, offset: int = 0, db=Depends(get_db)):
    """Get query history."""
    try:
        query = db.query(Query)
        if recruiter_id:
            query = query.filter(Query.recruiter_id == recruiter_id)

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
async def get_dashboard_metrics(recruiter_id: str = None, db=Depends(get_db)):
    """Get dashboard metrics."""
    try:
        from ..database import Lead, Query
        from sqlalchemy import func

        # Today's leads
        today = datetime.utcnow().date()
        today_leads = db.query(func.count(Lead.id)).filter(
            func.date(Lead.created_at) == today
        ).scalar() or 0

        # Total leads
        total_leads = db.query(func.count(Lead.id)).scalar() or 0

        # Average score
        avg_score = db.query(func.avg(Lead.score)).scalar() or 0.0

        # Recent queries
        recent_queries = db.query(Query).order_by(Query.created_at.desc()).limit(5).all()

        # Top companies by leads
        top_companies = db.query(
            Lead.company_name,
            func.count(Lead.id).label('count')
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
async def get_usage_metrics(period: str = "30d", recruiter_id: str = None, db=Depends(get_db)):
    """Get usage metrics."""
    try:
        from ..database import Query, Lead
        from sqlalchemy import func

        # Parse period
        days = int(period.rstrip('d'))

        # Date filter
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Usage stats
        total_queries = db.query(func.count(Query.id)).filter(
            Query.created_at >= cutoff_date
        ).scalar() or 0

        total_cost = db.query(func.sum(Query.total_cost)).filter(
            Query.created_at >= cutoff_date
        ).scalar() or 0.0

        successful_queries = db.query(func.count(Query.id)).filter(
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
async def get_performance_metrics(db=Depends(get_db)):
    """Get performance metrics."""
    try:
        from ..database import Query, Lead
        from sqlalchemy import func

        # Average execution time
        avg_execution_time = db.query(func.avg(Query.execution_time)).scalar() or 0.0

        # Average lead score
        avg_lead_score = db.query(func.avg(Lead.score)).scalar() or 0.0

        # Query success rate
        total_queries = db.query(func.count(Query.id)).scalar() or 0
        successful_queries = db.query(func.count(Query.id)).filter(
            Query.processing_status == "completed"
        ).scalar() or 0

        success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0

        # Leads per query
        total_leads = db.query(func.count(Lead.id)).scalar() or 0
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
