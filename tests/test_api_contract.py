
import pytest
import asyncio
from app.services.pipeline import RecruiterPipeline
from app.intelligence.intelligence_engine import IntelligenceEngine
from app.routes.recruiter import IntelligenceMetadata, IntelligenceSignals, QueryResponse
from unittest.mock import AsyncMock, patch, MagicMock

# Global patch for SessionLocal to prevent DB access in any test
@pytest.fixture(autouse=True)
def mock_session_local():
    with patch("app.services.pipeline.SessionLocal") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock

# ==========================================
# API Contract Tests
# ==========================================

@pytest.mark.asyncio
async def test_intelligence_schema_validation():
    """Verify processing returns valid IntelligenceMetadata and IntelligenceSignals."""
    pipeline = RecruiterPipeline()
    await pipeline.initialize()
    
    # Mock components to isolate intelligence engine output
    mock_orch = AsyncMock()
    mock_orch.orchestrate_search.return_value = {"confidence": 0.9, "total_steps": 1, "total_cost": 0, "evidence_objects": []}
    pipeline.action_orchestrator = mock_orch
    pipeline.signal_judge = AsyncMock()
    pipeline.signal_judge.judge_leads.return_value = []
    pipeline._save_to_database = AsyncMock()
    
    query = "Hiring Senior Backend Engineers in San Francisco"
    
    # Run pipeline
    result = await pipeline.process_recruiter_query(query)
    
    # 1. Check dictionary structure
    assert "intelligence" in result
    assert "signals" in result
    
    # 2. Validate against Pydantic models (Strict Contract)
    intel_data = result["intelligence"]
    signals_data = result["signals"]
    
    # Should not raise validation error
    intel_model = IntelligenceMetadata(**intel_data)
    signals_model = IntelligenceSignals(**signals_data)
    
    # 3. Valid field checks
    assert "Backend" in intel_model.role
    assert "San Francisco" in intel_model.location
    assert intel_model.seniority == "Senior"
    
    # 4. Signal Ranges [0, 1]
    assert 0.0 <= signals_model.hiring_pressure <= 1.0
    assert 0.0 <= signals_model.role_scarcity <= 1.0
    
    print("✅ Schema Validation Passed")

@pytest.mark.asyncio
async def test_output_determinism():
    """Verify that same query produces IDENTICAL intelligence and signals."""
    pipeline = RecruiterPipeline()
    await pipeline.initialize()
    
    # Mocks
    pipeline.action_orchestrator = AsyncMock()
    pipeline.action_orchestrator.orchestrate_search.return_value = {"confidence":0,"total_steps":0,"total_cost":0,"evidence_objects":[]}
    pipeline.signal_judge = AsyncMock()
    pipeline.signal_judge.judge_leads.return_value = []
    pipeline._save_to_database = AsyncMock()
    
    query = "Lead Data Scientist remote"
    
    result1 = await pipeline.process_recruiter_query(query)
    result2 = await pipeline.process_recruiter_query(query)
    
    # Deep equality check
    assert result1["intelligence"] == result2["intelligence"]
    assert result1["signals"] == result2["signals"]
    
    print("✅ Determinism Passed")

@pytest.mark.asyncio
async def test_backward_compatibility():
    """Verify concept_vector legacy field still exists."""
    pipeline = RecruiterPipeline()
    await pipeline.initialize()
    
     # Mocks
    pipeline.action_orchestrator = AsyncMock()
    pipeline.action_orchestrator.orchestrate_search.return_value = {"confidence":0,"total_steps":0,"total_cost":0,"evidence_objects":[]}
    pipeline.signal_judge = AsyncMock()
    pipeline.signal_judge.judge_leads.return_value = []
    pipeline._save_to_database = AsyncMock()
    
    result = await pipeline.process_recruiter_query("test query")
    
    assert "concept_vector" in result
    assert isinstance(result["concept_vector"], dict)
    
    print("✅ Backward Compatibility Passed")

