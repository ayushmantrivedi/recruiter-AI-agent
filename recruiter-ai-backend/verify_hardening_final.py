"""
Production Hardening Verification
Final end-to-end test of all hardening changes
"""

import asyncio
import uuid
from datetime import datetime
from app.services.pipeline import recruiter_pipeline
from app.database import SessionLocal, Query, Lead
from app.utils.logger import get_logger

logger = get_logger("hardening_verification")

async def verify_all_fixes():
    """Verify all production hardening fixes."""
    logger.info("=" * 60)
    logger.info("PRODUCTION HARDENING VERIFICATION")
    logger.info("=" * 60)
    
    query_text = "senior data engineer in Pune"
    query_id = str(uuid.uuid4())
    
    # Create DB record
    db = SessionLocal()
    try:
        query_record = Query(
            id=query_id,
            recruiter_id="hardening-test",
            query_text=query_text,
            processing_status="processing",
            created_at=datetime.utcnow()
        )
        db.add(query_record)
        db.commit()
    finally:
        db.close()
    
    # Execute pipeline
    logger.info("Executing pipeline...")
    result = await recruiter_pipeline.process_recruiter_query(
        query_text,
        recruiter_id="hardening-test",
        query_id=query_id
    )
    
    # Verify pipeline completed
    assert result["status"] == "completed"
    logger.info("✓ Pipeline completed successfully")
    
    leads = result.get("leads", [])
    total_leads_found = result.get("total_leads_found", 0)
    
    # TEST 1: total_leads_found accuracy
    logger.info(f"\n📊 TEST 1: total_leads_found Accuracy")
    logger.info(f"   Leads returned: {len(leads)}")
    logger.info(f"   total_leads_found: {total_leads_found}")
    assert total_leads_found == len(leads), \
        f"total_leads_found ({total_leads_found}) != len(leads) ({len(leads)})"
    logger.info("   ✅ PASS: Counts match")
    
    # TEST 2: No duplicates
    logger.info(f"\n📊 TEST 2: Deduplication")
    seen_keys = set()
    duplicates = 0
    for lead in leads:
        key = (
            lead.get("company_name", "").lower(),
            lead.get("role", "").lower(),
            lead.get("location", "").lower()
        )
        if key in seen_keys:
            duplicates += 1
        seen_keys.add(key)
    
    assert duplicates == 0, f"Found {duplicates} duplicate leads"
    logger.info(f"   Unique leads: {len(seen_keys)}")
    logger.info("   ✅ PASS: No duplicates")
    
    # TEST 3: Score distribution
    logger.info(f"\n📊 TEST 3: Score Distribution")
    scores = [l.get("score", 0) for l in leads]
    if scores:
        max_score = max(scores)
        min_score = min(scores)
        avg_score = sum(scores) / len(scores)
        
        logger.info(f"   Max score: {max_score:.1f}")
        logger.info(f"   Min score: {min_score:.1f}")
        logger.info(f"   Avg score: {avg_score:.1f}")
        logger.info(f"   Spread: {max_score - min_score:.1f}")
        
        assert max_score < 100.0, f"Max score ({max_score}) should not reach 100"
        logger.info("   ✅ PASS: No saturation at 100")
    
    # TEST 4: Reasons populated
    logger.info(f"\n📊 TEST 4: Reasons Population")
    leads_with_reasons = 0
    for lead in leads:
        if "reasons" in lead and len(lead["reasons"]) > 0:
            leads_with_reasons += 1
    
    logger.info(f"   Leads with reasons: {leads_with_reasons}/{len(leads)}")
    assert leads_with_reasons == len(leads), "All leads should have reasons"
    logger.info("   ✅ PASS: All leads have reasons")
    
    # Show sample reasons
    if leads:
        logger.info(f"\n   Sample reasons from top lead:")
        for reason in leads[0].get("reasons", [])[:3]:
            logger.info(f"      - {reason}")
    
    # TEST 5: Database persistence
    logger.info(f"\n📊 TEST 5: Database Persistence")
    db = SessionLocal()
    try:
        saved_leads = db.query(Lead).filter(Lead.query_id == query_id).all()
        logger.info(f"   Leads saved to DB: {len(saved_leads)}")
        assert len(saved_leads) > 0, "No leads saved to database"
        
        # Verify all have required fields
        for lead in saved_leads:
            assert lead.company_name is not None
            assert lead.score is not None
            assert lead.confidence is not None
            assert lead.reasons is not None
        
        logger.info("   ✅ PASS: All leads persisted with required fields")
    finally:
        db.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 ALL HARDENING VERIFICATIONS PASSED")
    logger.info("=" * 60 + "\n")
    
    # Summary
    logger.info("SUMMARY:")
    logger.info(f"  ✅ total_leads_found accuracy: VERIFIED")
    logger.info(f"  ✅ Deduplication: VERIFIED")
    logger.info(f"  ✅ Score soft cap: VERIFIED")
    logger.info(f"  ✅ Reasons population: VERIFIED")
    logger.info(f"  ✅ Database persistence: VERIFIED")

async def main():
    """Run hardening verification."""
    try:
        await verify_all_fixes()
    except Exception as e:
        logger.error(f"❌ VERIFICATION FAILED: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
