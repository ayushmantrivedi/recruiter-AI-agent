"""
Lead Persistence Verification
Verifies enriched leads are successfully saved to database
"""

import asyncio
import uuid
from datetime import datetime
from app.services.pipeline import recruiter_pipeline
from app.database import SessionLocal, Query, Lead
from app.utils.logger import get_logger

logger = get_logger("persistence_verification")

async def test_leads_saved_to_database():
    """Verify enriched leads are successfully persisted."""
    logger.info("=" * 60)
    logger.info("LEAD PERSISTENCE VERIFICATION")
    logger.info("=" * 60)
    
    query_text = "senior python developer in Pune"
    query_id = str(uuid.uuid4())
    
    # Create DB record
    db = SessionLocal()
    try:
        query_record = Query(
            id=query_id,
            recruiter_id="persistence-test",
            query_text=query_text,
            processing_status="processing",
            created_at=datetime.utcnow()
        )
        db.add(query_record)
        db.commit()
        logger.info(f"✓ Created query record: {query_id}")
    finally:
        db.close()
    
    # Execute pipeline
    logger.info("Executing pipeline...")
    result = await recruiter_pipeline.process_recruiter_query(
        query_text,
        recruiter_id="persistence-test",
        query_id=query_id
    )
    
    # Verify pipeline completed
    assert result["status"] == "completed", f"Pipeline failed: {result.get('error')}"
    logger.info(f"✓ Pipeline completed successfully")
    
    # Verify leads in result
    result_leads = result.get("leads", [])
    logger.info(f"✓ Pipeline returned {len(result_leads)} leads")
    
    # Verify leads were saved to DB
    db = SessionLocal()
    try:
        saved_leads = db.query(Lead).filter(Lead.query_id == query_id).all()
        
        logger.info(f"\n📊 PERSISTENCE RESULTS:")
        logger.info(f"   Leads returned by pipeline: {len(result_leads)}")
        logger.info(f"   Leads saved to database: {len(saved_leads)}")
        
        if len(saved_leads) == 0:
            logger.error("❌ ZERO LEADS SAVED - Enrichment or validation failed!")
            logger.error("Checking for SKIPPING warnings in logs...")
            return False
        
        logger.info(f"\n✅ SUCCESS: {len(saved_leads)} leads persisted")
        
        # Verify lead data
        for i, lead in enumerate(saved_leads[:5], 1):
            logger.info(f"\n   Lead {i}:")
            logger.info(f"      Company: {lead.company_name}")
            logger.info(f"      Score: {lead.score}")
            logger.info(f"      Confidence: {lead.confidence}")
            logger.info(f"      Reasons: {len(lead.reasons)} items")
        
        # Verify no fields are None
        for lead in saved_leads:
            assert lead.company_name is not None, "company_name is None"
            assert lead.score is not None, "score is None"
            assert lead.confidence is not None, "confidence is None"
        
        logger.info(f"\n✅ All leads have required fields")
        
    finally:
        db.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 PERSISTENCE VERIFICATION PASSED")
    logger.info("=" * 60 + "\n")
    return True

async def main():
    """Run persistence verification."""
    try:
        success = await test_leads_saved_to_database()
        if not success:
            raise RuntimeError("Persistence verification failed")
    except Exception as e:
        logger.error(f"❌ VERIFICATION FAILED: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
