
import sys
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.append(os.getcwd())

async def run_debug():
    print("DEBUG CONTRACT START")
    try:
        from app.services.pipeline import RecruiterPipeline
        from app.routes.recruiter import IntelligenceMetadata, IntelligenceSignals
        
        # Patch SessionLocal
        with patch("app.services.pipeline.SessionLocal") as mock_db:
             mock_instance = MagicMock()
             mock_db.return_value = mock_instance
             
             pipeline = RecruiterPipeline()
             await pipeline.initialize()
             print("Pipeline Initialized")
             
             # Mock components
             mock_orch = AsyncMock()
             mock_orch.orchestrate_search.return_value = {"confidence": 0.9, "total_steps": 1, "total_cost": 0, "evidence_objects": []}
             pipeline.action_orchestrator = mock_orch
             pipeline.signal_judge = AsyncMock()
             pipeline.signal_judge.judge_leads.return_value = []
             pipeline._save_to_database = AsyncMock()
             
             query = "Hiring Senior Backend Engineers in San Francisco"
             
             print("Processing...")
             try:
                 result = await pipeline.process_recruiter_query(query)
                 print("Result keys:", result.keys())
                 
                 if "intelligence" in result:
                     print("Intelligence:", result["intelligence"])
                     model = IntelligenceMetadata(**result["intelligence"])
                     print("Intelligence Model Valid validated")
                 else:
                     print("FAIL: intelligence key missing")
                     
                 if "signals" in result:
                     print("Signals:", result["signals"])
                     signals = IntelligenceSignals(**result["signals"])
                     print("Signals Model Validated")
                 else:
                     print("FAIL: signals key missing")
                     
                 if "concept_vector" in result:
                     print("Concept Vector Present")
                 else:
                     print("FAIL: concept_vector key missing")
                     
             except Exception as e:
                 print(f"Process Failed: {e}")
                 import traceback
                 traceback.print_exc()

    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_debug())
