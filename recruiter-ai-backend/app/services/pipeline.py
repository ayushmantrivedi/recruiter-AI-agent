import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
# from ..agents.concept_reasoner import concept_reasoner # Removed
from ..search.search_orchestrator import search_orchestrator
from ..database import SessionLocal, Query, Lead, AgentExecution
from ..utils.logger import get_logger
from ..utils.cache import cache

from ..intelligence.intelligence_engine import IntelligenceEngine

logger = get_logger("pipeline")


class RecruiterPipeline:
    """Main pipeline service orchestrating the complete agent workflow."""

    def __init__(self):
        self.search_orchestrator = search_orchestrator
        self.intelligence_engine = IntelligenceEngine

    async def initialize(self):
        """Initialize all agents and verify pipeline integrity."""
        # 1. Verify Intelligence Engine
        if not hasattr(self, "intelligence_engine") or not self.intelligence_engine:
            raise RuntimeError("CRITICAL: IntelligenceEngine missing in RecruiterPipeline")
            
        # 2. Verify Search Orchestrator
        if not self.search_orchestrator:
             raise RuntimeError("CRITICAL: SearchOrchestrator missing in RecruiterPipeline")

        # 3. Verify Database (simple check to ensure import/connection capability)
             
        # 4. Verify Database (simple check to ensure import/connection capability)
        try:
            from ..database import SessionLocal
            db = SessionLocal()
            db.close()
        except Exception as e:
            raise RuntimeError(f"CRITICAL: Database adapter failed: {str(e)}")

        # Ensure no legacy ghosts exist
        if hasattr(self, "concept_reasoner"):
            delattr(self, "concept_reasoner")

        logger.info("Recruiter pipeline initialized and verified")

    async def process_recruiter_query(self, recruiter_query: str, recruiter_id: str = None, query_id: str = None) -> Dict[str, Any]:
        """Process a complete recruiter query through all agents.

        Args:
            recruiter_query: Raw recruiter search query
            recruiter_id: Optional recruiter ID for personalization

        Returns:
            Complete processing results with leads
        """
        # Use provided query_id or generate new one
        if query_id is None:
            query_id = str(uuid.uuid4())

        start_time = datetime.utcnow()

        try:
            logger.info("Starting recruiter query processing",
                       query_id=query_id,
                       recruiter_id=recruiter_id,
                       query=recruiter_query)

            # Step 1: Intelligence Engine (Deterministic)
            logger.info("Step 1: Intelligence Engine", query_id=query_id)
            intelligence_result = self.intelligence_engine.process(recruiter_query)
            
            # Split into Metadata and Signals for API contract
            intelligence = {
                "intent": intelligence_result.intent,
                "role": intelligence_result.role,
                "skills": intelligence_result.skills,
                "experience": intelligence_result.experience,
                "seniority": intelligence_result.seniority,
                "location": intelligence_result.location
            }
            
            signals = {
                "hiring_pressure": intelligence_result.hiring_pressure,
                "role_scarcity": intelligence_result.role_scarcity,
                "outsourcing_likelihood": intelligence_result.outsourcing_likelihood,
                "market_difficulty": intelligence_result.market_difficulty
            }

            # Map to legacy format for compatibility (full dict)
            concept_vector = intelligence_result.dict()
            
            # Extract constraints from intelligence result
            constraints = {
                "role": intelligence_result.role,
                "location": intelligence_result.location,
                "experience": intelligence_result.experience,
                "seniority": intelligence_result.seniority,
                "skills": intelligence_result.skills
            }

            # Step 2: Search & Ranking Orchestration (New Layer)
            logger.info("Step 2: Search & Ranking Orchestration", query_id=query_id)
            
            # Prepare intelligence envelope
            intelligence_envelope = {
                "intelligence": intelligence,
                "signals": signals
            }
            
            search_result = await self.search_orchestrator.orchestrate(
                recruiter_query,
                intelligence_envelope
            )

            # Map results
            leads = search_result["leads"]
            evidence_objects = search_result["evidence_objects"]
            
            # CRITICAL FIX: Get total_count BEFORE limiting
            # This is the count from orchestrator before any truncation
            total_leads_before_limit = search_result["total_count"]
            
            # Limit to top 20 leads for API response
            limited_leads = leads[:20]
            
            # Contract validation: total_leads_found must be >= len(limited_leads)
            if total_leads_before_limit < len(limited_leads):
                logger.error("CONTRACT VIOLATION: total_leads_found < len(leads)",
                           total=total_leads_before_limit,
                           actual=len(limited_leads))
                # Fix the violation
                total_leads_before_limit = len(limited_leads)
            
            # Get deduplication metrics from orchestrator
            # (Now integrated into ExecutionReport)
            
            # Orchestration Summary - Use the canonical ExecutionReport
            execution_report = search_result.get("execution_report")
            
            if execution_report:
                # Update report with pipeline-level context
                execution_report.query_id = query_id
                execution_report.leads_saved = len(limited_leads) # Intended save count
                
                # Use report as the summary
                orchestration_summary = execution_report.__dict__
            else:
                # Fallback (Should not happen with new Orchestrator)
                orchestration_summary = search_result.get("orchestration_summary", {})

            # Calculate final metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            result = {
                "query_id": query_id,
                "recruiter_id": recruiter_id,
                "original_query": recruiter_query,
                "processing_time": processing_time,
                "concept_vector": concept_vector,
                "intelligence": intelligence,
                "signals": signals,
                "constraints": constraints,
                
                # Canonical Contracts
                "orchestration_summary": orchestration_summary,
                "total_leads_found": execution_report.raw_leads_found if execution_report else len(leads),
                "leads": limited_leads,
                
                # Internal Pass-through for DB persistence
                "execution_report_dto": execution_report,
                
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat()
            }

            # Save to database
            await self._save_to_database(result)

            logger.info("Recruiter query processing completed",
                       query_id=query_id,
                       leads_found=len(leads),
                       processing_time=processing_time)

            return result

        except Exception as e:
            logger.error("Pipeline processing failed",
                        error=str(e),
                        query_id=query_id,
                        query=recruiter_query)

            # Update database status to failed
            try:
                db = SessionLocal()
                query_record = db.query(Query).filter(Query.id == query_id).first()
                if query_record:
                    query_record.processing_status = "failed"
                    query_record.execution_time = (datetime.utcnow() - start_time).total_seconds()
                    db.commit()
                db.close()
            except Exception as db_error:
                logger.error("Failed to update job status to failed",
                            error=str(db_error),
                            query_id=query_id)

            # Return error result
            return {
                "query_id": query_id,
                "recruiter_id": recruiter_id,
                "original_query": recruiter_query,
                "status": "failed",
                "error": str(e),
                "leads": [],
                "processing_time": (datetime.utcnow() - start_time).total_seconds()
            }

    async def _save_to_database(self, result: Dict[str, Any]):
        """Save processing results to database with guaranteed consistency."""
        import traceback

        db_session = None
        try:
            logger.info("💾 DB_SAVE_STARTED", query_id=result["query_id"])
            db_session = SessionLocal()

            # Update OR Create query record (Upsert)
            query = db_session.query(Query).filter(Query.id == result["query_id"]).first()
            
            if not query:
                logger.info("🆕 CREATING_NEW_QUERY_RECORD", query_id=result["query_id"])
                # Create new record (Sync path or new test)
                query = Query(id=result["query_id"])
                db_session.add(query)
            else:
                logger.info("📝 UPDATING_EXISTING_QUERY_RECORD", query_id=result["query_id"])

            # Common fields update
            query.recruiter_id = result.get("recruiter_id")
            query.query_text = result["original_query"]
            query.concept_vector = result["concept_vector"]
            query.intelligence = result.get("intelligence")
            query.signals = result.get("signals")
            query.constraints = result["constraints"]
            query.confidence_score = result["orchestration_summary"]["confidence"] if "confidence" in result["orchestration_summary"] else 0.0
            
            # Prioritize lead max confidence if summary is missing it (ExecutionReport vs Legacy)
            if not query.confidence_score and result.get("leads"):
                 query.confidence_score = max([l.get("confidence", 0) for l in result["leads"]])
            
            query.processing_status = "completed"
            query.total_cost = 0.0
            query.execution_time = result["processing_time"]
            query.completed_at = datetime.utcnow()

            # Save Execution Report
            if "execution_report_dto" in result:
                from ..database import ExecutionReport
                dto = result["execution_report_dto"]
                db_report = ExecutionReport(
                    query_id=result["query_id"],
                    raw_leads_found=dto.raw_leads_found,
                    normalized_leads=dto.normalized_leads,
                    ranked_leads_count=dto.ranked_leads_count,
                    leads_saved=dto.leads_saved, # Passed from result
                    deduplicated_count=dto.deduplicated_count,
                    skipped_invalid_count=dto.skipped_invalid_count,
                    providers_called=dto.providers_called,
                    providers_succeeded=dto.providers_succeeded,
                    providers_failed=dto.providers_failed,
                    provider_diagnostics=dto.provider_diagnostics,
                    execution_time_ms=dto.execution_time_ms,
                    execution_mode=dto.execution_mode
                )
                db_session.add(db_report)
                logger.info("📊 DB_SAVE_EXECUTION_REPORT", query_id=result["query_id"])


            # Save leads with error handling
            logger.info("👥 DB_SAVE_LEADS_STARTED",
                       query_id=result["query_id"],
                       lead_count=len(result["leads"]))
            
            from ..contracts.lead_contract import LeadContract
            
            leads_saved = 0
            for lead_data in result["leads"]:
                try:
                    # 1. Contract Enforcement - Strip unknown fields
                    clean_lead = LeadContract.sanitize(lead_data)
                    if not clean_lead:
                        logger.warning("⚠️ SKIPPING_INVALID_LEAD", 
                                     query_id=result["query_id"], 
                                     reason="contract_validation_failed")
                        continue
                    
                    # 2. Verify required fields
                    if not LeadContract.validate_required(clean_lead):
                        logger.warning("⚠️ SKIPPING_LEAD_MISSING_REQUIRED_FIELDS",
                                     query_id=result["query_id"],
                                     company=clean_lead.get("company_name", "unknown"))
                        continue
                        
                    # 3. Persist (only DB-allowed fields)
                    lead = Lead(
                        query_id=result["query_id"],
                        company_name=clean_lead["company_name"],
                        score=clean_lead["score"],
                        confidence=clean_lead["confidence"],
                        reasons=clean_lead.get("reasons", []),
                        # NOTE: evidence_count removed - not in DB schema
                        evidence_objects=clean_lead.get("evidence_objects", []),
                        job_postings=clean_lead.get("job_postings", []),
                        news_mentions=clean_lead.get("news_mentions", [])
                    )
                    db_session.add(lead)
                    leads_saved += 1
                except Exception as lead_error:
                    logger.error("❌ FAILED_TO_SAVE_LEAD",
                               query_id=result["query_id"],
                               company=lead_data.get("company", "unknown"),
                               error=str(lead_error))

            # Commit all changes atomically
            logger.info("🔄 DB_TRANSACTION_COMMIT_STARTED", query_id=result["query_id"])
            db_session.commit()
            logger.info("✅ DB_TRANSACTION_COMMIT_COMPLETED",
                       query_id=result["query_id"],
                       leads_saved=leads_saved)

            db_session.close()
            db_session = None

            logger.info("💾 DB_SAVE_COMPLETED_SUCCESSFULLY",
                       query_id=result["query_id"],
                       leads_saved=leads_saved)

        except Exception as e:
            logger.error("💥 DB_SAVE_FAILED",
                        error=str(e),
                        query_id=result["query_id"],
                        traceback=traceback.format_exc())

            # Attempt to rollback and mark job as failed
            if db_session:
                try:
                    db_session.rollback()
                    # Try to mark job as failed
                    query = db_session.query(Query).filter(Query.id == result["query_id"]).first()
                    if query:
                        query.processing_status = "failed"
                        query.execution_time = result.get("processing_time", 0)
                        db_session.commit()
                        logger.info("❌ JOB_MARKED_AS_FAILED_DUE_TO_DB_ERROR", query_id=result["query_id"])
                except Exception as rollback_error:
                    logger.error("💥 DB_ROLLBACK_FAILED",
                               query_id=result["query_id"],
                               rollback_error=str(rollback_error))
                finally:
                    try:
                        db_session.close()
                    except:
                        pass

            # Re-raise to let caller handle
            raise

    async def get_query_status(self, query_id: str) -> Optional[Dict[str, Any]]:
        """Get the status and results of a query."""
        try:
            logger.info("Pipeline get_query_status called", query_id=query_id)

            # Check cache first
            cached_result = await cache.get(f"query_result:{query_id}")
            if cached_result:
                logger.info("Found cached result", query_id=query_id)
                return cached_result

            # Check database
            db = SessionLocal()
            try:
                logger.info("Querying database", query_id=query_id)
                query = db.query(Query).filter(Query.id == query_id).first()
                logger.info("Database query result", query_id=query_id, found=query is not None)

                if not query:
                    return None

                # Get associated leads
                leads = db.query(Lead).filter(Lead.query_id == query_id).all()
                
                # CRITICAL FIX: Get total_leads_found from ExecutionReport
                from ..database import ExecutionReport as DBExecutionReport
                execution_report = db.query(DBExecutionReport).filter(
                    DBExecutionReport.query_id == query_id
                ).first()
                
                # Determine total_leads_found from ExecutionReport (canonical source)
                if execution_report:
                    total_leads_found = execution_report.raw_leads_found
                    orchestration_summary = {
                        "raw_leads_found": execution_report.raw_leads_found,
                        "normalized_leads": execution_report.normalized_leads,
                        "ranked_leads_count": execution_report.ranked_leads_count,
                        "leads_saved": execution_report.leads_saved,
                        "providers_called": execution_report.providers_called,
                        "providers_succeeded": execution_report.providers_succeeded,
                        "providers_failed": execution_report.providers_failed,
                        "execution_time_ms": execution_report.execution_time_ms,
                        "execution_mode": execution_report.execution_mode
                    }
                else:
                    # Fallback: use len(leads) if no ExecutionReport
                    total_leads_found = len(leads)
                    orchestration_summary = None
                    logger.warning("No ExecutionReport found, using fallback", query_id=query_id)
                
                # CONTRACT INVARIANT: If leads exist, total_leads_found MUST be > 0
                if len(leads) > 0 and total_leads_found == 0:
                    error_msg = f"CONTRACT VIOLATION: len(leads)={len(leads)} but total_leads_found=0"
                    logger.critical(error_msg, query_id=query_id)
                    raise RuntimeError(error_msg)

                result = {
                    "query_id": query_id,
                    "status": query.processing_status,
                    "original_query": query.query_text,
                    "concept_vector": query.concept_vector,
                    "intelligence": query.intelligence,
                    "signals": query.signals,
                    "constraints": query.constraints,
                    "confidence_score": query.confidence_score,
                    "total_cost": query.total_cost,
                    "execution_time": query.execution_time,
                    "orchestration_summary": orchestration_summary,
                    "total_leads_found": total_leads_found,  # CRITICAL: Was missing!
                    "leads": [
                        {
                            "company": lead.company_name,
                            "score": lead.score,
                            "confidence": lead.confidence,
                            "reasons": lead.reasons
                            # evidence_count removed - not in DB schema
                        }
                        for lead in leads
                    ],
                    "completed_at": query.completed_at.isoformat() if query.completed_at else None
                }

                # Cache for 1 hour
                await cache.set(f"query_result:{query_id}", result, ttl=3600)

                return result

            finally:
                db.close()

        except Exception as e:
            logger.error("Query status retrieval failed", error=str(e), query_id=query_id)
            return None

    async def get_recruiter_stats(self, recruiter_id: str) -> Dict[str, Any]:
        """Get statistics for a recruiter."""
        try:
            db = SessionLocal()
            try:
                # Query stats
                query_count = db.query(Query).filter(Query.recruiter_id == recruiter_id).count()
                lead_count = db.query(Lead).join(Query).filter(Query.recruiter_id == recruiter_id).count()

                # Average scores
                from sqlalchemy import func
                avg_score = db.query(func.avg(Lead.score)).join(Query).filter(Query.recruiter_id == recruiter_id).scalar() or 0.0

                # Total cost
                total_cost = db.query(func.sum(Query.total_cost)).filter(Query.recruiter_id == recruiter_id).scalar() or 0.0

                return {
                    "recruiter_id": recruiter_id,
                    "total_queries": query_count,
                    "total_leads": lead_count,
                    "average_lead_score": round(avg_score, 2),
                    "total_cost": round(total_cost, 2),
                    "leads_per_query": round(lead_count / query_count, 2) if query_count > 0 else 0.0
                }

            finally:
                db.close()

        except Exception as e:
            logger.error("Recruiter stats retrieval failed", error=str(e), recruiter_id=recruiter_id)
            return {
                "recruiter_id": recruiter_id,
                "error": str(e)
            }


# Global pipeline instance
recruiter_pipeline = RecruiterPipeline()
