
import sys
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.append(os.getcwd())

async def run_repro():
    print("REPRO START")
    try:
        from app.services.pipeline import RecruiterPipeline
        from app.intelligence.intelligence_engine import IntelligenceResult
        
        # Patch SessionLocal
        with patch("app.services.pipeline.SessionLocal") as mock_db:
             mock_instance = MagicMock()
             mock_db.return_value = mock_instance
             
             pipeline = RecruiterPipeline()
             await pipeline.initialize()
             
             # Mock Intelligence Engine
             pipeline.intelligence_engine.process = MagicMock(return_value=IntelligenceResult(
                intent="hiring", role="Engineer", skills=["Python"], experience=5, seniority="Senior", location="Remote",
                hiring_pressure=0.8, role_scarcity=0.7, outsourcing_likelihood=0.1, market_difficulty=0.6
             ))
             
             pipeline._save_to_database = AsyncMock()
             
             # Mock Job API Manager
             with patch("app.search.data_sources.job_api_manager") as mock_job_api:
                mock_job_api.search_jobs = AsyncMock(return_value=[
                    {"company": "MockCompany", "title": "MockRole", "url": "http://mock.com"}
                ])
                
                print("Running process_recruiter_query...")
                result = await pipeline.process_recruiter_query("Hiring Python Dev")
                print("Process completed")
                
                if result["status"] != "completed":
                    print(f"FAIL: Status is {result['status']}")
                
                if "leads" not in result:
                    print("FAIL: Leads missing")
                    
                print("REPRO SUCCESS")
                
    except Exception as e:
        print(f"REPRO FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_repro())
