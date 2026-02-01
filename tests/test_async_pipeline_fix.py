import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.pipeline import RecruiterPipeline
from app.routes.recruiter import process_query_background

@pytest.fixture
def mock_pipeline():
    with patch("app.routes.recruiter.recruiter_pipeline") as mock:
        # Mock components
        mock.intelligence_engine = MagicMock()
        mock.search_orchestrator = AsyncMock()
        
        # Mock intelligence engine return
        mock_intel = MagicMock()
        mock_intel.dict.return_value = {"role": "Engineer"}
        mock_intel.intent = "hiring"
        mock_intel.role = "Engineer"
        mock_intel.skills = ["Python"]
        mock_intel.experience = 5
        mock_intel.seniority = "Senior"
        mock_intel.location = "Remote"
        
        # Signals
        mock_intel.hiring_pressure = 0.5
        mock_intel.role_scarcity = 0.8
        mock_intel.outsourcing_likelihood = 0.2
        mock_intel.market_difficulty = 0.7
        
        mock.intelligence_engine.process.return_value = mock_intel
        
        # Mock search orchestrator return
        mock.search_orchestrator.orchestrate.return_value = {
            "leads": [{"company": "Foo", "confidence": 0.9, "score": 85, "reasons": [], "evidence_count": 1}],
            "evidence_objects": [],
            "total_count": 1
        }
        
        # Mock db save
        mock._save_to_database = AsyncMock()
        
        yield mock

@pytest.mark.asyncio
async def test_async_pipeline_execution_calls_orchestrator(mock_pipeline):
    """Verify that process_query_background calls pipeline correctly."""
    
    query_id = "test-query-id"
    query = "Hire a python dev"
    recruiter_id = "recruiter-1"
    
    # Mock return for process_recruiter_query
    mock_pipeline.process_recruiter_query = AsyncMock(return_value={"status": "completed"})
    
    # We need to mock SessionLocal as well since process_query_background uses it
    with patch("app.routes.recruiter.SessionLocal") as mock_session_local:
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        await process_query_background(query_id, query, recruiter_id)
    
    # Check pipeline called
    mock_pipeline.process_recruiter_query.assert_called_once_with(
        query,
        recruiter_id,
        query_id=query_id
    )

def test_pipeline_interface_integrity():
    """Verify RecruiterPipeline class exposes required attributes."""
    # We import the real class here, not mocked instance
    from app.services.pipeline import RecruiterPipeline
    
    pipeline = RecruiterPipeline()
    assert hasattr(pipeline, "search_orchestrator")
    assert hasattr(pipeline, "intelligence_engine")
    # Should NOT have legacy attributes
    assert not hasattr(pipeline, "action_orchestrator")
