
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.pipeline import RecruiterPipeline
from app.intelligence.intelligence_engine import IntelligenceResult

# Global patch for SessionLocal
@pytest.fixture(autouse=True)
def mock_session_local():
    with patch("app.services.pipeline.SessionLocal") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock

def test_pipeline_integration_with_search():
    async def run_async_test():
        pipeline = RecruiterPipeline()
        await pipeline.initialize()
        
        # Mock components
        pipeline.intelligence_engine.process = MagicMock(return_value=IntelligenceResult(
            intent="hiring", role="Engineer", skills=["Python"], experience=5, seniority="Senior", location="Remote",
            hiring_pressure=0.8, role_scarcity=0.7, outsourcing_likelihood=0.1, market_difficulty=0.6
        ))
        
        # Mock DB save
        pipeline._save_to_database = AsyncMock()
        
        # Mock Job API Manager to avoid network calls
        with patch("app.search.data_sources.job_api_manager") as mock_job_api:
            mock_job_api.search_jobs = AsyncMock(return_value=[
                {"company": "MockCompany", "title": "MockRole", "url": "http://mock.com"}
            ])
            
            result = await pipeline.process_recruiter_query("Hiring Python Dev")
            
            assert result["status"] == "completed"
            assert "leads" in result
            assert "orchestration_summary" in result
            assert result["orchestration_summary"]["confidence"] >= 0
            assert len(result["leads"]) > 0
            
            # Check if leads have scores
            first_lead = result["leads"][0]
            assert "score" in first_lead
            assert "company" in first_lead
            
            # Verify DB save was called
            pipeline._save_to_database.assert_called_once()
            
            # Verify structure matches API contract
            assert "intelligence" in result
            assert "signals" in result

    import asyncio
    asyncio.run(run_async_test())
