import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.pipeline import RecruiterPipeline
from app.routes.recruiter import _execute_pipeline_with_checkpoint

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
async def test_async_pipeline_execution_calls_search_orchestrator(mock_pipeline):
    """Verify that _execute_pipeline_with_checkpoint calls search_orchestrator correctly."""
    
    query_id = "test-query-id"
    query = "Hire a python dev"
    recruiter_id = "recruiter-1"
    
    await _execute_pipeline_with_checkpoint(query_id, query, recruiter_id)
    
    # Check Intelligence Engine called
    mock_pipeline.intelligence_engine.process.assert_called_once_with(query)
    
    # Check Search Orchestrator called (instead of action_orchestrator)
    mock_pipeline.search_orchestrator.orchestrate.assert_called_once()
    
    # Verify call args
    call_args = mock_pipeline.search_orchestrator.orchestrate.call_args
    assert call_args[0][0] == query # query arg
    assert "intelligence" in call_args[0][1] # intelligence_envelope arg
    assert "signals" in call_args[0][1]
    
    # Verify DB save called
    mock_pipeline._save_to_database.assert_called_once()
    saved_data = mock_pipeline._save_to_database.call_args[0][0]
    assert saved_data["query_id"] == query_id
    assert saved_data["status"] == "completed"

def test_pipeline_interface_integrity():
    """Verify RecruiterPipeline class exposes required attributes."""
    # We import the real class here, not mocked instance
    from app.services.pipeline import RecruiterPipeline
    
    pipeline = RecruiterPipeline()
    assert hasattr(pipeline, "search_orchestrator")
    assert hasattr(pipeline, "intelligence_engine")
    # Should NOT have legacy attributes
    assert not hasattr(pipeline, "action_orchestrator")
