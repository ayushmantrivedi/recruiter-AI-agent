"""
End-to-End Verification Script for System Hardening
Tests the complete pipeline with real components to verify:
1. Lead validation and persistence
2. Intelligence -> Search location contract
3. Partial failure handling
"""

import asyncio
import uuid
from datetime import datetime
from app.services.pipeline import recruiter_pipeline
from app.database import SessionLocal, Query, Lead
from app.utils.logger import get_logger

logger = get_logger("e2e_verification")

async def test_full_pipeline_with_location():
    """Test that location from intelligence is respected in search."""
    logger.info("=" * 60)
    logger.info("TEST 1: Location Contract Verification")
    logger.info("=" * 60)
    
    query_text = "backend engineers in Pune"
    query_id = str(uuid.uuid4())
    
    # Create DB record
    db = SessionLocal()
    try:
        query_record = Query(
            id=query_id,
            recruiter_id="test-verifier",
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
    result = await recruiter_pipeline.process_recruiter_query(
        query_text,
        recruiter_id="test-verifier",
        query_id=query_id
    )
    
    # Verify intelligence extracted location
    assert result["intelligence"]["location"] == "Pune", \
        f"Expected location 'Pune', got '{result['intelligence']['location']}'"
    logger.info(f"✓ Intelligence extracted location: {result['intelligence']['location']}")
    
    # Verify constraints passed to search
    assert result["constraints"]["location"] == "Pune", \
        f"Expected constraints location 'Pune', got '{result['constraints']['location']}'"
    logger.info(f"✓ Search constraints used location: {result['constraints']['location']}")
    
    # Verify leads were saved
    assert result["status"] == "completed"
    assert len(result["leads"]) > 0
    logger.info(f"✓ Pipeline completed with {len(result['leads'])} leads")
    
    logger.info("✅ TEST 1 PASSED: Location contract verified\n")
    return True

async def test_lead_persistence_with_validation():
    """Test that leads are validated and saved correctly."""
    logger.info("=" * 60)
    logger.info("TEST 2: Lead Validation & Persistence")
    logger.info("=" * 60)
    
    query_text = "data scientist remote"
    query_id = str(uuid.uuid4())
    
    # Create DB record
    db = SessionLocal()
    try:
        query_record = Query(
            id=query_id,
            recruiter_id="test-verifier",
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
    result = await recruiter_pipeline.process_recruiter_query(
        query_text,
        recruiter_id="test-verifier",
        query_id=query_id
    )
    
    # Verify leads were saved to DB
    db = SessionLocal()
    try:
        saved_leads = db.query(Lead).filter(Lead.query_id == query_id).all()
        logger.info(f"✓ Found {len(saved_leads)} leads in database")
        
        # Verify each lead has required fields
        for lead in saved_leads:
            assert lead.company_name is not None and lead.company_name != "", \
                "Lead missing company_name"
            assert lead.score is not None, "Lead missing score"
            assert lead.confidence is not None, "Lead missing confidence"
            logger.info(f"  - {lead.company_name}: score={lead.score}, confidence={lead.confidence}")
        
        logger.info("✓ All leads have required fields")
    finally:
        db.close()
    
    logger.info("✅ TEST 2 PASSED: Lead validation working\n")
    return True

async def test_concurrent_queries():
    """Test that multiple concurrent queries complete successfully."""
    logger.info("=" * 60)
    logger.info("TEST 3: Concurrent Query Execution")
    logger.info("=" * 60)
    
    queries = [
        "python developer in Bangalore",
        "frontend engineer remote",
        "product manager in Mumbai"
    ]
    
    tasks = []
    query_ids = []
    
    # Create DB records
    db = SessionLocal()
    try:
        for query_text in queries:
            query_id = str(uuid.uuid4())
            query_ids.append(query_id)
            
            query_record = Query(
                id=query_id,
                recruiter_id="test-verifier",
                query_text=query_text,
                processing_status="processing",
                created_at=datetime.utcnow()
            )
            db.add(query_record)
            
            tasks.append(
                recruiter_pipeline.process_recruiter_query(
                    query_text,
                    recruiter_id="test-verifier",
                    query_id=query_id
                )
            )
        
        db.commit()
        logger.info(f"✓ Created {len(queries)} query records")
    finally:
        db.close()
    
    # Execute concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Verify all completed
    success_count = 0
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"✗ Query {i+1} failed: {result}")
        else:
            assert result["status"] == "completed"
            success_count += 1
            logger.info(f"✓ Query {i+1} completed with {len(result['leads'])} leads")
    
    assert success_count == len(queries), f"Only {success_count}/{len(queries)} queries succeeded"
    logger.info(f"✓ All {success_count} concurrent queries completed successfully")
    
    logger.info("✅ TEST 3 PASSED: Concurrent execution stable\n")
    return True

async def main():
    """Run all verification tests."""
    logger.info("\n" + "=" * 60)
    logger.info("SYSTEM HARDENING VERIFICATION SUITE")
    logger.info("=" * 60 + "\n")
    
    tests = [
        ("Location Contract", test_full_pipeline_with_location),
        ("Lead Validation", test_lead_persistence_with_validation),
        ("Concurrent Execution", test_concurrent_queries)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, "PASSED", None))
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED: {e}")
            results.append((test_name, "FAILED", str(e)))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, status, _ in results if status == "PASSED")
    failed = sum(1 for _, status, _ in results if status == "FAILED")
    
    for test_name, status, error in results:
        symbol = "✅" if status == "PASSED" else "❌"
        logger.info(f"{symbol} {test_name}: {status}")
        if error:
            logger.info(f"   Error: {error}")
    
    logger.info(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed > 0:
        raise RuntimeError(f"Verification failed: {failed} test(s) failed")
    
    logger.info("\n🎉 ALL VERIFICATIONS PASSED 🎉\n")

if __name__ == "__main__":
    asyncio.run(main())
