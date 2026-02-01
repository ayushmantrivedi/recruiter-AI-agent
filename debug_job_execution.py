
import sys
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock

sys.path.append(os.getcwd())

async def run_debug():
    print("DEBUG JOB EXECUTION START")
    try:
        from app.services.pipeline import RecruiterPipeline
        from app.intelligence.intelligence_engine import IntelligenceEngine
        
        pipeline = RecruiterPipeline()
        await pipeline.initialize()
        
        # MOCKING
        # Create a mock for orchestration
        mock_orch = AsyncMock()
        mock_orch.orchestrate_search.return_value = {
            "confidence": 0.9, 
            "total_steps": 1, 
            "total_cost": 0,
            "evidence_objects": [{"title": "Dev"}] 
        }
        pipeline.action_orchestrator = mock_orch
        
        # Create a mock for judge
        mock_judge = AsyncMock()
        mock_judge.judge_leads.return_value = [{"company": "TestCo", "score": 95, "confidence": 0.9, "reasons": [], "evidence_count": 1}]
        pipeline.signal_judge = mock_judge
        
        # Ensure database methods are mocked or work
        # process_recruiter_query calls _save_to_database
        pipeline._save_to_database = AsyncMock()
        
        print("Mocks setup complete")
        
        query = "Find senior AI engineers in Bangalore"
        
        # execute
        print("Executing process_recruiter_query...")
        result = await pipeline.process_recruiter_query(query)
        
        print("Result Status:", result.get("status"))
        print("Concept Vector Keys:", result.get("concept_vector", {}).keys())
        
        if result["status"] == "completed":
             print("✅ Job Execution SUCCESS")
        else:
             print("❌ Job Execution FAILED")
             print(result)

    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_debug())
