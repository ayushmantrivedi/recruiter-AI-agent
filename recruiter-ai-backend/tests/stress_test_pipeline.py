import asyncio
import uuid
import time
from typing import Dict, Any
from app.services.pipeline import recruiter_pipeline
from app.routes.recruiter import _execute_pipeline_with_checkpoint
from app.utils.logger import get_logger

logger = get_logger("stress_test")

async def run_stress_test(num_concurrent_jobs: int = 5):
    """Run concurrent pipeline executions to test reliability."""
    logger.info("🚀 STARTING STRESS TEST", num_jobs=num_concurrent_jobs)
    
    test_queries = [
        "Senior Python Backend Engineer in Remote",
        "Data Scientist matching generic pattern",
        "Frontend Developer with React expertise",
        "Product Manager for AI startup",
        "DevOps Engineer with Kubernetes experience"
    ]
    
    tasks = []
    
    # Pre-create jobs in DB
    from app.database import SessionLocal, Query
    from datetime import datetime
    
    db = SessionLocal()
    try:
        for i in range(num_concurrent_jobs):
            query_id = str(uuid.uuid4())
            # Cycle through test queries
            query_text = test_queries[i % len(test_queries)]
            recruiter_id = "test-recruiter-id"

            # Create record
            query_record = Query(
                id=query_id,
                recruiter_id=recruiter_id,
                query_text=query_text,
                processing_status="processing",
                created_at=datetime.utcnow()
            )
            db.add(query_record)
            
            logger.info(f"Scheduling job {i+1}", query_id=query_id)
            
            # We test the background execution function directly to simulate async workers
            tasks.append(
                _execute_pipeline_with_checkpoint(query_id, query_text, recruiter_id)
            )
        
        db.commit()
    except Exception as e:
        logger.error("Failed to seed database", error=str(e))
        db.rollback()
        return
    finally:
        db.close()
    
    start_time = time.time()
    
    # Execute concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    success_count = 0
    failure_count = 0
    
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            logger.error(f"Job {i+1} FAILED", error=str(res))
            failure_count += 1
        else:
            success_count += 1
            
    logger.info("📊 STRESS TEST RESULTS", 
                total_jobs=num_concurrent_jobs,
                success=success_count,
                failures=failure_count,
                total_time_seconds=round(total_time, 2),
                avg_time_per_job=round(total_time/num_concurrent_jobs, 2))
                
    if failure_count > 0:
        logger.error("❌ STRESS TEST FAILED with errors")
        raise RuntimeError(f"Stress test failed: {failure_count} errors")
    else:
        logger.info("✅ STRESS TEST PASSED")

if __name__ == "__main__":
    asyncio.run(run_stress_test(num_concurrent_jobs=10))
