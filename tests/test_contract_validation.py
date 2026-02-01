"""
Production Hardening Tests - Contract Validation
Tests for total_leads_found accuracy and API contract compliance
"""

import pytest
import asyncio
from app.intelligence.intelligence_engine import IntelligenceEngine
from app.search.search_orchestrator import SearchOrchestrator


@pytest.mark.asyncio
async def test_total_leads_found_accuracy():
    """Verify total_leads_found equals actual lead count."""
    query = "senior python developer in Bangalore"
    
    # Get intelligence
    intel_result = IntelligenceEngine.process(query)
    
    intelligence_envelope = {
        "intelligence": {
            "role": intel_result.role,
            "seniority": intel_result.seniority,
            "location": intel_result.location,
            "skills": intel_result.skills
        },
        "signals": {
            "hiring_pressure": intel_result.hiring_pressure,
            "role_scarcity": intel_result.role_scarcity,
            "market_difficulty": intel_result.market_difficulty,
            "outsourcing_likelihood": intel_result.outsourcing_likelihood
        }
    }
    
    # Run orchestrator
    orchestrator = SearchOrchestrator()
    result = await orchestrator.orchestrate(query, intelligence_envelope)
    
    leads = result["leads"]
    total_count = result["total_count"]
    
    # CRITICAL: total_count must equal len(leads)
    assert total_count == len(leads), f"total_count ({total_count}) must equal len(leads) ({len(leads)})"


@pytest.mark.asyncio
async def test_total_leads_found_greater_or_equal():
    """Verify total_leads_found >= len(leads) invariant."""
    query = "machine learning engineer"
    
    intel_result = IntelligenceEngine.process(query)
    
    intelligence_envelope = {
        "intelligence": {
            "role": intel_result.role,
            "seniority": intel_result.seniority,
            "location": intel_result.location,
            "skills": intel_result.skills
        },
        "signals": {
            "hiring_pressure": intel_result.hiring_pressure,
            "role_scarcity": intel_result.role_scarcity,
            "market_difficulty": intel_result.market_difficulty,
            "outsourcing_likelihood": intel_result.outsourcing_likelihood
        }
    }
    
    orchestrator = SearchOrchestrator()
    result = await orchestrator.orchestrate(query, intelligence_envelope)
    
    total_count = result["total_count"]
    actual_count = len(result["leads"])
    
    # Invariant: total >= actual
    assert total_count >= actual_count, f"total_leads_found ({total_count}) must be >= len(leads) ({actual_count})"


@pytest.mark.asyncio
async def test_api_response_has_required_fields():
    """Verify API response contains all required fields."""
    query = "data analyst"
    
    intel_result = IntelligenceEngine.process(query)
    
    intelligence_envelope = {
        "intelligence": {
            "role": intel_result.role,
            "seniority": intel_result.seniority,
            "location": intel_result.location,
            "skills": intel_result.skills
        },
        "signals": {
            "hiring_pressure": intel_result.hiring_pressure,
            "role_scarcity": intel_result.role_scarcity,
            "market_difficulty": intel_result.market_difficulty,
            "outsourcing_likelihood": intel_result.outsourcing_likelihood
        }
    }
    
    orchestrator = SearchOrchestrator()
    result = await orchestrator.orchestrate(query, intelligence_envelope)
    
    # Required fields
    assert "leads" in result
    assert "total_count" in result
    assert "evidence_objects" in result
    assert "top_companies" in result
    assert "metrics" in result
    
    # Verify types
    assert isinstance(result["leads"], list)
    assert isinstance(result["total_count"], int)
    assert isinstance(result["evidence_objects"], list)
    assert isinstance(result["top_companies"], list)
    assert isinstance(result["metrics"], dict)


@pytest.mark.asyncio
async def test_deduplication_metrics_present():
    """Verify deduplication metrics are included in response."""
    query = "software engineer"
    
    intel_result = IntelligenceEngine.process(query)
    
    intelligence_envelope = {
        "intelligence": {
            "role": intel_result.role,
            "seniority": intel_result.seniority,
            "location": intel_result.location,
            "skills": intel_result.skills
        },
        "signals": {
            "hiring_pressure": intel_result.hiring_pressure,
            "role_scarcity": intel_result.role_scarcity,
            "market_difficulty": intel_result.market_difficulty,
            "outsourcing_likelihood": intel_result.outsourcing_likelihood
        }
    }
    
    orchestrator = SearchOrchestrator()
    result = await orchestrator.orchestrate(query, intelligence_envelope)
    
    metrics = result["metrics"]
    
    # Required metrics
    assert "raw_leads_fetched" in metrics
    assert "normalized_leads" in metrics
    assert "scored_leads" in metrics
    assert "unique_leads" in metrics
    assert "duplicates_removed" in metrics
    assert "duplicate_rate" in metrics
    
    # Verify types
    assert isinstance(metrics["raw_leads_fetched"], int)
    assert isinstance(metrics["normalized_leads"], int)
    assert isinstance(metrics["scored_leads"], int)
    assert isinstance(metrics["unique_leads"], int)
    assert isinstance(metrics["duplicates_removed"], int)
    assert isinstance(metrics["duplicate_rate"], float)
    
    # Verify logic
    assert metrics["duplicates_removed"] >= 0
    assert 0.0 <= metrics["duplicate_rate"] <= 1.0


@pytest.mark.asyncio
async def test_lead_has_required_fields():
    """Verify each lead has required fields."""
    query = "backend developer"
    
    intel_result = IntelligenceEngine.process(query)
    
    intelligence_envelope = {
        "intelligence": {
            "role": intel_result.role,
            "seniority": intel_result.seniority,
            "location": intel_result.location,
            "skills": intel_result.skills
        },
        "signals": {
            "hiring_pressure": intel_result.hiring_pressure,
            "role_scarcity": intel_result.role_scarcity,
            "market_difficulty": intel_result.market_difficulty,
            "outsourcing_likelihood": intel_result.outsourcing_likelihood
        }
    }
    
    orchestrator = SearchOrchestrator()
    result = await orchestrator.orchestrate(query, intelligence_envelope)
    
    leads = result["leads"]
    
    if len(leads) > 0:
        for lead in leads:
            # Required fields
            assert "company_name" in lead, "Lead missing company_name"
            assert "score" in lead, "Lead missing score"
            assert "confidence" in lead, "Lead missing confidence"
            assert "reasons" in lead, "Lead missing reasons"
            
            # Verify types
            assert isinstance(lead["company_name"], str)
            assert isinstance(lead["score"], (int, float))
            assert isinstance(lead["confidence"], (int, float))
            assert isinstance(lead["reasons"], list)
            
            # Verify values
            assert lead["company_name"], "Company name should not be empty"
            assert 0 <= lead["score"] <= 100
            assert 0.4 <= lead["confidence"] <= 0.95
            assert len(lead["reasons"]) > 0


@pytest.mark.asyncio
async def test_no_duplicate_companies_in_output():
    """Verify no duplicate companies in final output."""
    query = "full stack engineer"
    
    intel_result = IntelligenceEngine.process(query)
    
    intelligence_envelope = {
        "intelligence": {
            "role": intel_result.role,
            "seniority": intel_result.seniority,
            "location": intel_result.location,
            "skills": intel_result.skills
        },
        "signals": {
            "hiring_pressure": intel_result.hiring_pressure,
            "role_scarcity": intel_result.role_scarcity,
            "market_difficulty": intel_result.market_difficulty,
            "outsourcing_likelihood": intel_result.outsourcing_likelihood
        }
    }
    
    orchestrator = SearchOrchestrator()
    result = await orchestrator.orchestrate(query, intelligence_envelope)
    
    leads = result["leads"]
    
    # Check for duplicates by (company, role, location)
    seen_keys = set()
    for lead in leads:
        company = lead.get("company_name", "").lower().strip()
        role = lead.get("role", "").lower().strip()
        location = lead.get("location", "").lower().strip()
        
        key = (company, role, location)
        
        assert key not in seen_keys, f"Duplicate found: {key}"
        seen_keys.add(key)


@pytest.mark.asyncio
async def test_score_distribution_has_variance():
    """Verify scores have meaningful variance."""
    query = "devops engineer"
    
    intel_result = IntelligenceEngine.process(query)
    
    intelligence_envelope = {
        "intelligence": {
            "role": intel_result.role,
            "seniority": intel_result.seniority,
            "location": intel_result.location,
            "skills": intel_result.skills
        },
        "signals": {
            "hiring_pressure": intel_result.hiring_pressure,
            "role_scarcity": intel_result.role_scarcity,
            "market_difficulty": intel_result.market_difficulty,
            "outsourcing_likelihood": intel_result.outsourcing_likelihood
        }
    }
    
    orchestrator = SearchOrchestrator()
    result = await orchestrator.orchestrate(query, intelligence_envelope)
    
    leads = result["leads"]
    
    if len(leads) > 1:
        scores = [lead["score"] for lead in leads]
        
        # Verify no score reaches 100
        assert max(scores) < 100.0, f"Max score ({max(scores)}) should be < 100"
        
        # Verify spread
        score_range = max(scores) - min(scores)
        assert score_range > 0, "Scores should have some variance"
