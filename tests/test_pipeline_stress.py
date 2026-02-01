import pytest
import asyncio
from typing import Dict, Any
from app.search.lead_validator import LeadValidator
from app.search.lead_normalizer import LeadNormalizer
from app.search.search_orchestrator import SearchOrchestrator
from app.services.pipeline import recruiter_pipeline

@pytest.mark.asyncio
async def test_lead_validator_fixes_missing_company():
    """Verify LeadValidator defaults missing company."""
    invalid_lead = {
        "title": "Engineer",
        "score": 85,
        "confidence": 0.9,
    }
    
    fixed = LeadValidator.validate_and_fix(invalid_lead)
    assert fixed is not None
    assert fixed["company"] == "Unknown Company"
    assert fixed["company_name"] == "Unknown Company"

@pytest.mark.asyncio
async def test_lead_validator_enforces_numeric_types():
    """Verify numeric fields are clamped and typed correctly."""
    bad_types = {
        "company": "Test Co",
        "score": "95.5", # String
        "confidence": 1.5 # Over 1.0
    }
    
    fixed = LeadValidator.validate_and_fix(bad_types)
    assert fixed is not None
    assert isinstance(fixed["score"], float)
    assert fixed["score"] == 95.5
    assert fixed["confidence"] == 1.0 # Clamped

@pytest.mark.asyncio
async def test_search_orchestrator_respects_location_contract():
    """Verify location is not overridden if provided by intelligence."""
    orchestrator = SearchOrchestrator()
    query = "dev"
    
    # Case 1: Intelligence provides location
    intel_data = {
        "intelligence": {"location": "Pune", "role": "dev"},
        "signals": {}
    }
    
    # We mock the sources fetch to check constraints passed to it
    from unittest.mock import AsyncMock
    original_sources = orchestrator.sources
    mock_source = AsyncMock()
    mock_source.fetch.return_value = []
    orchestrator.sources = [mock_source]
    
    await orchestrator.orchestrate(query, intel_data)
    
    # Verify constraints passed to source
    call_args = mock_source.fetch.call_args
    constraints = call_args[0][1] # second arg
    assert constraints["location"] == "Pune"
    
    # Case 2: Intelligence missing location -> Fallback to Remote
    intel_data_empty = {
        "intelligence": {"role": "dev"}, # No location
        "signals": {}
    }
    await orchestrator.orchestrate(query, intel_data_empty)
    call_args = mock_source.fetch.call_args
    constraints = call_args[0][1]
    assert constraints["location"] == "Remote"
    
    # Restore
    orchestrator.sources = original_sources

@pytest.mark.asyncio
async def test_pipeline_validation_gate_unit():
    """Verify LeadValidator is called and filters invalid leads."""
    from app.search.lead_validator import LeadValidator
    
    # Test 1: Valid lead passes through
    valid_lead = {"company": "Test Co", "score": 85, "confidence": 0.9}
    result = LeadValidator.validate_and_fix(valid_lead)
    assert result is not None
    assert result["company"] == "Test Co"
    
    # Test 2: Missing company gets defaulted
    missing_company = {"score": 85, "confidence": 0.9}
    result = LeadValidator.validate_and_fix(missing_company)
    assert result is not None
    assert result["company"] == "Unknown Company"
    
    # Test 3: Non-dict gets rejected
    invalid_structure = "not a dict"
    result = LeadValidator.validate_and_fix(invalid_structure)
    assert result is None
    
    # Test 4: Numeric validation
    bad_numbers = {"company": "Test", "score": "invalid", "confidence": 2.0}
    result = LeadValidator.validate_and_fix(bad_numbers)
    assert result is not None
    assert result["score"] == 0.0  # Invalid score defaulted
    assert result["confidence"] == 1.0  # Clamped

@pytest.mark.asyncio
async def test_end_to_end_location_contract():
    """Integration test: Verify location flows from intelligence to search."""
    from app.intelligence.intelligence_engine import IntelligenceEngine
    from app.search.search_orchestrator import SearchOrchestrator
    
    # Test query with specific location
    query = "backend engineers in Pune"
    
    # Step 1: Intelligence extraction
    intel_result = IntelligenceEngine.process(query)
    assert intel_result.location == "Pune"
    
    # Step 2: Prepare envelope
    intelligence_envelope = {
        "intelligence": {
            "location": intel_result.location,
            "role": intel_result.role,
            "skills": intel_result.skills
        },
        "signals": {}
    }
    
    # Step 3: Mock orchestrator sources to verify constraints
    from unittest.mock import AsyncMock
    orchestrator = SearchOrchestrator()
    original_sources = orchestrator.sources
    mock_source = AsyncMock()
    mock_source.fetch.return_value = []
    orchestrator.sources = [mock_source]
    
    await orchestrator.orchestrate(query, intelligence_envelope)
    
    # Verify location was passed correctly
    call_args = mock_source.fetch.call_args
    constraints = call_args[0][1]
    assert constraints["location"] == "Pune", f"Expected 'Pune' but got '{constraints['location']}'"
    
    # Restore
    orchestrator.sources = original_sources
