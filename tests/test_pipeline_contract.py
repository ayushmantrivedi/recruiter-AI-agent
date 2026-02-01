"""
Pipeline Contract Tests
Verifies data contract enforcement and schema compliance
"""

import pytest
import asyncio
from app.contracts.lead_contract import LeadContract
from app.search.search_orchestrator import SearchOrchestrator
from app.intelligence.intelligence_engine import IntelligenceEngine

def test_lead_contract_strips_unknown_fields():
    """Verify LeadContract strips fields not in DB schema."""
    lead_with_extra_fields = {
        "company": "Test Co",
        "score": 85,
        "confidence": 0.9,
        "evidence_count": 5,  # NOT in DB schema
        "title": "Engineer",  # NOT in DB schema
        "location": "Pune",  # NOT in DB schema
        "unknown_field": "value"  # NOT in DB schema
    }
    
    clean = LeadContract.sanitize(lead_with_extra_fields)
    
    assert clean is not None
    assert "company_name" in clean  # Normalized from 'company'
    assert "score" in clean
    assert "confidence" in clean
    
    # These should be stripped
    assert "evidence_count" not in clean
    assert "title" not in clean
    assert "location" not in clean
    assert "unknown_field" not in clean

def test_lead_contract_normalizes_company_field():
    """Verify 'company' is normalized to 'company_name'."""
    lead = {"company": "Acme Corp", "score": 90, "confidence": 0.95}
    clean = LeadContract.sanitize(lead)
    
    assert clean["company_name"] == "Acme Corp"
    assert "company" not in clean  # Original key removed

def test_lead_contract_defaults_missing_company():
    """Verify missing company gets defaulted."""
    lead = {"score": 80, "confidence": 0.8}
    clean = LeadContract.sanitize(lead)
    
    assert clean is not None
    assert clean["company_name"] == "Unknown Company"

def test_lead_contract_validates_required_fields():
    """Verify required field validation."""
    valid_lead = {"company_name": "Test", "score": 85, "confidence": 0.9}
    assert LeadContract.validate_required(valid_lead) is True
    
    invalid_lead = {"company_name": "Test", "score": 85}  # Missing confidence
    assert LeadContract.validate_required(invalid_lead) is False

def test_lead_contract_clamps_numeric_values():
    """Verify score and confidence are clamped."""
    lead = {
        "company": "Test",
        "score": 150,  # Over 100
        "confidence": 2.5  # Over 1.0
    }
    
    clean = LeadContract.sanitize(lead)
    assert clean["score"] == 100.0  # Clamped
    assert clean["confidence"] == 1.0  # Clamped

def test_lead_contract_ensures_json_fields_are_lists():
    """Verify JSON fields default to empty lists."""
    lead = {"company": "Test", "score": 85, "confidence": 0.9}
    clean = LeadContract.sanitize(lead)
    
    assert isinstance(clean["reasons"], list)
    assert isinstance(clean["evidence_objects"], list)
    assert isinstance(clean["job_postings"], list)
    assert isinstance(clean["news_mentions"], list)

@pytest.mark.asyncio
async def test_location_contract_end_to_end():
    """Integration test: Verify location flows from intelligence to search."""
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
    
    # Step 3: Mock orchestrator to verify constraints
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
    assert constraints["location"] == "Pune", \
        f"Location contract violated: expected 'Pune', got '{constraints['location']}'"
    
    # Restore
    orchestrator.sources = original_sources

def test_schema_drift_protection():
    """Verify unknown fields don't break DB inserts."""
    # Simulate future code adding new fields
    future_lead = {
        "company": "Future Corp",
        "score": 95,
        "confidence": 0.98,
        "new_field_v2": "some_value",
        "another_future_field": 123
    }
    
    clean = LeadContract.sanitize(future_lead)
    
    # Should only have DB-allowed fields
    assert "new_field_v2" not in clean
    assert "another_future_field" not in clean
    assert clean["company_name"] == "Future Corp"

@pytest.mark.asyncio
async def test_partial_failure_handling():
    """Verify valid leads are saved even when some are invalid."""
    from app.contracts.lead_contract import LeadContract
    
    leads = [
        {"company": "Valid Co 1", "score": 85, "confidence": 0.9},
        "invalid_structure",  # Will be rejected
        {"company": "Valid Co 2", "score": 90, "confidence": 0.95},
        {"score": 80},  # Missing company, will be defaulted
        {"company": "Valid Co 3", "score": 88, "confidence": 0.92}
    ]
    
    valid_count = 0
    for lead in leads:
        clean = LeadContract.sanitize(lead)
        if clean and LeadContract.validate_required(clean):
            valid_count += 1
    
    # Should have 4 valid (3 explicit + 1 with defaulted company)
    assert valid_count == 4
