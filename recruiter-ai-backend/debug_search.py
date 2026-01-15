
import sys
import os
import asyncio
from unittest.mock import MagicMock, patch

sys.path.append(os.getcwd())

async def run_debug():
    print("DEBUG SEARCH LAYER START")
    try:
        from app.services.pipeline import RecruiterPipeline
        
        # Patch SessionLocal to avoid DB
        with patch("app.services.pipeline.SessionLocal") as mock_db:
             mock_instance = MagicMock()
             mock_db.return_value = mock_instance
             
             pipeline = RecruiterPipeline()
             await pipeline.initialize()
             print("Pipeline Initialized")
             
             # Mock Intelligence Engine to avoid complex logic if needed, 
             # but we can try using the real one if it's deterministic and fast.
             # The real one is imported in pipeline.py.
             
             # Let's mock _save_to_database to mock DB interaction
             pipeline._save_to_database = MagicMock()
             async def mock_save(result):
                 print("Mock DB Save called")
             pipeline._save_to_database = mock_save
             
             query = "Hiring Senior Python Engineer in Berlin"
             print(f"Processing query: {query}")
             
             result = await pipeline.process_recruiter_query(query)
             
             print("Result Status:", result.get("status"))
             print("Leads Found:", len(result.get("leads", [])))
             
             if result.get("leads"):
                 print("Top Lead:", result["leads"][0])
                 print("Score:", result["leads"][0].get("score"))
                 print("Confidence:", result["leads"][0].get("confidence"))
             
             # Check orchestration summary
             print("Orchestration Summary:", result.get("orchestration_summary"))
             
             print("DEBUG SEARCH LAYER SUCCESS")

    except Exception as e:
        print(f"DEBUG SEARCH LAYER FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_debug())
