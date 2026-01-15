
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.pipeline import RecruiterPipeline, recruiter_pipeline
from app.intelligence.intelligence_engine import IntelligenceEngine

# Global patch for SessionLocal to prevent DB access in any test
@pytest.fixture(autouse=True)
def mock_session_local():
    with patch("app.services.pipeline.SessionLocal") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock

# ==========================================
# 1. Pipeline Integrity Tests
# ==========================================

@pytest.mark.asyncio
async def test_pipeline_composition():
    """Verify pipeline has correct components and no legacy ghosts."""
    pipeline = RecruiterPipeline()
    await pipeline.initialize()
    
    # Must have new engine
    assert hasattr(pipeline, "intelligence_engine")
    assert pipeline.intelligence_engine is not None
    
    # Must NOT have old agent
    assert not hasattr(pipeline, "concept_reasoner")

@pytest.mark.asyncio
async def test_startup_validation():
    """Verify startup fails if components are missing (simulated)."""
    pipeline = RecruiterPipeline()
    
    # Simulate broken state
    pipeline.intelligence_engine = None
    
    with pytest.raises(RuntimeError) as excinfo:
        await pipeline.initialize()
    assert "CRITICAL" in str(excinfo.value)
    assert "IntelligenceEngine missing" in str(excinfo.value)

# ==========================================
# 2. Job Execution Tests
# ==========================================

@pytest.mark.asyncio
async def test_job_structure_determinism():
    """Verify that processing a query yields populated concept inputs deterministically."""
    pipeline = RecruiterPipeline()
    await pipeline.initialize()
    
    # Mock orchestrator
    mock_orch = AsyncMock()
    mock_orch.orchestrate_search.return_value = {
        "confidence": 0.9, 
        "total_steps": 1, 
        "total_cost": 0,
        "evidence_objects": [{"title": "Dev"}] 
    }
    pipeline.action_orchestrator = mock_orch
    
    # Mock judge
    mock_judge = AsyncMock()
    mock_judge.judge_leads.return_value = [{"company": "TestCo", "score": 95, "confidence": 0.9, "reasons": [], "evidence_count": 1}]
    pipeline.signal_judge = mock_judge
    
    # Mock DB save
    pipeline._save_to_database = AsyncMock()
    
    query = "Find senior AI engineers in Bangalore"
    
    # Run 1
    result1 = await pipeline.process_recruiter_query(query)
    assert result1["status"] == "completed"
    assert "hiring_pressure" in result1["concept_vector"]
    assert result1["constraints"]["role"] == "AI Engineer"
    
    # Run 2 (Stability)
    result2 = await pipeline.process_recruiter_query(query)
    assert result1["concept_vector"] == result2["concept_vector"]
    assert result1["constraints"] == result2["constraints"]

# ==========================================
# 3. Stability Loop
# ==========================================

@pytest.mark.asyncio
async def test_stability_loop():
    """Run 10x to ensure no hidden state or randomness."""
    pipeline = RecruiterPipeline()
    await pipeline.initialize()
    
    mock_orch = AsyncMock()
    mock_orch.orchestrate_search.return_value = {"confidence":1, "total_steps":0, "total_cost":0, "evidence_objects":[]}
    pipeline.action_orchestrator = mock_orch
    
    mock_judge = AsyncMock()
    mock_judge.judge_leads.return_value = []
    pipeline.signal_judge = mock_judge
    
    pipeline._save_to_database = AsyncMock()

    query = "Find ML engineers in Pune"
    base_result = await pipeline.process_recruiter_query(query)
    
    for i in range(10):
        res = await pipeline.process_recruiter_query(query)
        # Check strict equality of the intelligence output
        assert res["concept_vector"] == base_result["concept_vector"]
        assert res["constraints"] == base_result["constraints"]

# ==========================================
# 4. Failure Handling
# ==========================================

@pytest.mark.asyncio
async def test_pipeline_failure_handling():
    """Verify that if Step 1 fails, the job fails gracefully."""
    pipeline = RecruiterPipeline()
    await pipeline.initialize()
    
    # Inject failure into IntelligenceEngine for this instance
    class BrokenEngine:
        def process(self, q):
            raise ValueError("Artificial Failure")
            
    pipeline.intelligence_engine = BrokenEngine()
    
    result = await pipeline.process_recruiter_query("test query")
    
    assert result["status"] == "failed"
    assert "Artificial Failure" in result["error"]


