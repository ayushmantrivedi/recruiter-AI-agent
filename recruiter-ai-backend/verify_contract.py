"""
Contract Verification - End-to-End Test
Verifies data contract enforcement in production pipeline
"""

import asyncio
import uuid
from datetime import datetime
from app.services.pipeline import recruiter_pipeline
from app.database import SessionLocal, Query, Lead
from app.utils.logger import get_logger

logger = get_logger("contract_verification")

async def test_evidence_count_stripped():
    """Verify evidence_count is stripped and doesn't cause DB errors."""
    logger.info("=" * 60)
    logger.info("TEST 1: evidence_count Field Stripping")
    logger.info("=" * 60)
    
    query_text = "python developer in Bangalore"
    query_id = str(uuid.uuid4())
    
    # Create DB record
    db = SessionLocal()
    try:
        query_record = Query(
            id=query_id,
            recruiter_id="contract-test",
            query_text=query_text,
            processing_status="processing",
            created_at=datetime.utcnow()
        )
        db.add(query_record)
        db.commit()
    finally:
        db.close()
    
    # Execute pipeline (will generate leads with evidence_count)
    result = await recruiter_pipeline.process_recruiter_query(
        query_text,
        recruiter_id="contract-test",
        query_id=query_id
    )
    
    # Verify pipeline completed
    assert result["status"] == "completed", f"Pipeline failed: {result.get('error')}"
    logger.info(f"✓ Pipeline completed successfully")
    
    # Verify leads were saved to DB
    db = SessionLocal()
    try:
        saved_leads = db.query(Lead).filter(Lead.query_id == query_id).all()
        assert len(saved_leads) > 0, "No leads saved to database"
        logger.info(f"✓ {len(saved_leads)} leads saved to database")
        
        # Verify no evidence_count errors
        for lead in saved_leads:
            # If this doesn't crash, evidence_count was properly stripped
            assert lead.company_name is not None
            logger.info(f"  - {lead.company_name}: score={lead.score}")
    finally:
        db.close()
    
    logger.info("✅ TEST 1 PASSED: evidence_count properly stripped\n")
    return True

async def test_location_contract():
    """Verify location from intelligence is used in search."""
    logger.info("=" * 60)
    logger.info("TEST 2: Location Contract Enforcement")
    logger.info("=" * 60)
    
    query_text = "data scientist in Pune"
    query_id = str(uuid.uuid4())
    
    # Create DB record
    db = SessionLocal()
    try:
        query_record = Query(
            id=query_id,
            recruiter_id="contract-test",
            query_text=query_text,
            processing_status="processing",
            created_at=datetime.utcnow()
        )
        db.add(query_record)
        db.commit()
    finally:
        db.close()
    
    # Execute pipeline
    result = await recruiter_pipeline.process_recruiter_query(
        query_text,
        recruiter_id="contract-test",
        query_id=query_id
    )
    
    # Verify intelligence extracted Pune
    assert result["intelligence"]["location"] == "Pune", \
        f"Intelligence failed to extract location: {result['intelligence']['location']}"
    logger.info(f"✓ Intelligence extracted: location={result['intelligence']['location']}")
    
    # Verify constraints used Pune
    assert result["constraints"]["location"] == "Pune", \
        f"Location contract violated: {result['constraints']['location']}"
    logger.info(f"✓ Search constraints used: location={result['constraints']['location']}")
    
    logger.info("✅ TEST 2 PASSED: Location contract enforced\n")
    return True

async def test_concurrent_queries_with_contract():
    """Verify contract enforcement works under concurrent load."""
    logger.info("=" * 60)
    logger.info("TEST 3: Concurrent Contract Enforcement")
    logger.info("=" * 60)
    
    queries = [
        "frontend engineer in Mumbai",
        "backend developer remote",
        "product manager in Delhi"
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
                recruiter_id="contract-test",
                query_text=query_text,
                processing_status="processing",
                created_at=datetime.utcnow()
            )
            db.add(query_record)
            
            tasks.append(
                recruiter_pipeline.process_recruiter_query(
                    query_text,
                    recruiter_id="contract-test",
                    query_id=query_id
                )
            )
        
        db.commit()
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
    
    assert success_count == len(queries)
    logger.info(f"✓ All {success_count} concurrent queries completed")
    
    logger.info("✅ TEST 3 PASSED: Contract enforcement stable under load\n")
    return True

async def main():
    """Run all contract verification tests."""
    logger.info("\n" + "=" * 60)
    logger.info("DATA CONTRACT VERIFICATION SUITE")
    logger.info("=" * 60 + "\n")
    
    tests = [
        ("evidence_count Stripping", test_evidence_count_stripped),
        ("Location Contract", test_location_contract),
        ("Concurrent Enforcement", test_concurrent_queries_with_contract)
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
        raise RuntimeError(f"Contract verification failed: {failed} test(s) failed")
    
    logger.info("\n🎉 ALL CONTRACT VERIFICATIONS PASSED 🎉\n")

if __name__ == "__main__":
    asyncio.run(main())
