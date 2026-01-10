import asyncio
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from ..agents.concept_reasoner import concept_reasoner
from ..agents.action_orchestrator import action_orchestrator
from ..agents.signal_judge import signal_judge
from ..database import SessionLocal, Query, Lead, AgentExecution
from ..utils.logger import get_logger
from ..utils.cache import cache

logger = get_logger("pipeline")


class RecruiterPipeline:
    """Main pipeline service orchestrating the complete agent workflow."""

    def __init__(self):
        self.concept_reasoner = concept_reasoner
        self.action_orchestrator = action_orchestrator
        self.signal_judge = signal_judge

    async def initialize(self):
        """Initialize all agents."""
        await self.concept_reasoner.initialize()
        logger.info("Recruiter pipeline initialized")

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

            # Step 1: Concept Reasoning
            logger.info("Step 1: Concept reasoning", query_id=query_id)
            concept_result = await self.concept_reasoner.process_query(recruiter_query, recruiter_id)
            concept_vector = concept_result["concept_vector"]
            constraints = concept_result["constraints"]

            # Step 2: Action Orchestration
            logger.info("Step 2: Action orchestration", query_id=query_id)
            orchestration_result = await self.action_orchestrator.orchestrate_search(
                query_id, concept_vector, constraints
            )

            evidence_objects = orchestration_result["evidence_objects"]

            # Step 3: Signal Judgment
            logger.info("Step 3: Signal judgment", query_id=query_id)
            leads = await self.signal_judge.judge_leads(query_id, evidence_objects, constraints)

            # Calculate final metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()

            result = {
                "query_id": query_id,
                "recruiter_id": recruiter_id,
                "original_query": recruiter_query,
                "processing_time": processing_time,
                "concept_vector": concept_vector,
                "constraints": constraints,
                "orchestration_summary": {
                    "confidence": orchestration_result["confidence"],
                    "total_steps": orchestration_result["total_steps"],
                    "total_cost": orchestration_result["total_cost"],
                    "evidence_count": len(evidence_objects)
                },
                "leads": leads[:20],  # Limit to top 20 leads
                "total_leads_found": len(leads),
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
        """Save processing results to database."""
        try:
            db = SessionLocal()
            try:
                # Update existing query record
                query = db.query(Query).filter(Query.id == result["query_id"]).first()
                if query:
                    # Update the existing record
                    query.concept_vector = result["concept_vector"]
                    query.constraints = result["constraints"]
                    query.confidence_score = result["orchestration_summary"]["confidence"]
                    query.processing_status = "completed"
                    query.total_cost = result["orchestration_summary"]["total_cost"]
                    query.execution_time = result["processing_time"]
                    query.completed_at = datetime.utcnow()
                else:
                    # Fallback: create new record if not found (shouldn't happen)
                    logger.warning("Query record not found, creating new one", query_id=result["query_id"])
                    query = Query(
                        id=result["query_id"],
                        recruiter_id=result.get("recruiter_id"),
                        query_text=result["original_query"],
                        concept_vector=result["concept_vector"],
                        constraints=result["constraints"],
                        confidence_score=result["orchestration_summary"]["confidence"],
                        processing_status="completed",
                        total_cost=result["orchestration_summary"]["total_cost"],
                        execution_time=result["processing_time"],
                        completed_at=datetime.utcnow()
                    )
                    db.add(query)

                # Save leads
                for lead_data in result["leads"]:
                    lead = Lead(
                        query_id=result["query_id"],
                        company_name=lead_data["company"],
                        score=lead_data["score"],
                        confidence=lead_data["confidence"],
                        reasons=lead_data["reasons"],
                        evidence_count=lead_data["evidence_count"]
                    )
                    db.add(lead)

                # Save execution history (simplified)
                # In production, would save detailed execution steps

                db.commit()
                logger.debug("Results saved to database", query_id=result["query_id"])

            finally:
                db.close()

        except Exception as e:
            logger.error("Database save failed", error=str(e), query_id=result["query_id"])

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

                result = {
                    "query_id": query_id,
                    "status": query.processing_status,
                    "original_query": query.query_text,
                    "concept_vector": query.concept_vector,
                    "constraints": query.constraints,
                    "confidence_score": query.confidence_score,
                    "total_cost": query.total_cost,
                    "execution_time": query.execution_time,
                    "leads": [
                        {
                            "company": lead.company_name,
                            "score": lead.score,
                            "confidence": lead.confidence,
                            "reasons": lead.reasons,
                            "evidence_count": lead.evidence_count
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
