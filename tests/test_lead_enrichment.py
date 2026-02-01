"""
Lead Enrichment Tests
Verifies enrichment layer injects required fields
"""

import pytest
from app.enrichment.lead_enricher import LeadEnricher
from app.contracts.lead_contract import LeadContract

def test_enrichment_fills_required_fields():
    """Verify enrichment adds score and confidence from confidence_score."""
    lead = {
        "company_name": "Test Co",
        "confidence_score": 85.0  # From scorer
    }
    
    intelligence = {"role": "Engineer", "seniority": "Senior", "location": "Pune"}
    signals = {"hiring_pressure": 0.8, "role_scarcity": 0.6}
    
    enriched = LeadEnricher.enrich(lead, intelligence, signals)
    
    assert "score" in enriched
    assert "confidence" in enriched
    assert enriched["score"] == 85.0
    assert enriched["confidence"] == 0.85  # 85/100

def test_enrichment_injects_intelligence_metadata():
    """Verify enrichment adds role, seniority, location."""
    lead = {"company_name": "Test Co", "confidence_score": 75.0}
    
    intelligence = {"role": "Backend Engineer", "seniority": "Mid-level", "location": "Mumbai"}
    signals = {}
    
    enriched = LeadEnricher.enrich(lead, intelligence, signals)
    
    assert enriched["role"] == "Backend Engineer"
    assert enriched["seniority"] == "Mid-level"
    assert enriched["location"] == "Mumbai"

def test_enrichment_does_not_overwrite_existing_fields():
    """Verify enrichment respects existing values."""
    lead = {
        "company_name": "Test Co",
        "score": 95.0,  # Already present
        "confidence": 0.98,  # Already present
        "role": "Existing Role"  # Already present
    }
    
    intelligence = {"role": "Different Role", "seniority": "Senior"}
    signals = {}
    
    enriched = LeadEnricher.enrich(lead, intelligence, signals)
    
    # Should NOT overwrite
    assert enriched["score"] == 95.0
    assert enriched["confidence"] == 0.98
    assert enriched["role"] == "Existing Role"
    
    # Should add missing
    assert enriched["seniority"] == "Senior"

def test_enriched_lead_passes_contract_validation():
    """Verify enriched leads pass LeadContract validation."""
    lead = {
        "company_name": "Valid Corp",
        "confidence_score": 88.0
    }
    
    intelligence = {"role": "Developer", "seniority": "Senior"}
    signals = {"hiring_pressure": 0.7}
    
    # Enrich
    enriched = LeadEnricher.enrich(lead, intelligence, signals)
    
    # Validate with contract
    clean = LeadContract.sanitize(enriched)
    
    assert clean is not None
    assert LeadContract.validate_required(clean)
    assert clean["company_name"] == "Valid Corp"
    assert clean["score"] == 88.0
    assert clean["confidence"] == 0.88

def test_enrichment_handles_missing_confidence_score():
    """Verify enrichment provides defaults when confidence_score missing."""
    lead = {"company_name": "Test Co"}  # No score
    
    intelligence = {"role": "Engineer"}
    signals = {}
    
    enriched = LeadEnricher.enrich(lead, intelligence, signals)
    
    # Should have defaults
    assert enriched["score"] == 50.0
    assert enriched["confidence"] == 0.5

def test_enrichment_batch_processing():
    """Verify batch enrichment works correctly."""
    leads = [
        {"company_name": "Co 1", "confidence_score": 90.0},
        {"company_name": "Co 2", "confidence_score": 75.0},
        {"company_name": "Co 3", "confidence_score": 85.0}
    ]
    
    intelligence = {"role": "Engineer", "seniority": "Senior"}
    signals = {"hiring_pressure": 0.8}
    
    enriched_batch = LeadEnricher.enrich_batch(leads, intelligence, signals)
    
    assert len(enriched_batch) == 3
    for enriched in enriched_batch:
        assert "score" in enriched
        assert "confidence" in enriched
        assert "role" in enriched

def test_enrichment_adds_company_alias():
    """Verify enrichment ensures both company and company_name exist."""
    lead = {"company_name": "Test Corp", "confidence_score": 80.0}
    
    enriched = LeadEnricher.enrich(lead, {}, {})
    
    # Should have both
    assert enriched["company_name"] == "Test Corp"
    assert enriched["company"] == "Test Corp"

@pytest.mark.asyncio
async def test_end_to_end_enrichment_in_pipeline():
    """Integration test: Verify enrichment works in full pipeline."""
    from app.intelligence.intelligence_engine import IntelligenceEngine
    from app.search.search_orchestrator import SearchOrchestrator
    
    query = "python developer in Bangalore"
    
    # Get intelligence
    intel_result = await IntelligenceEngine.process(query)
    
    intelligence_envelope = {
        "intelligence": {
            "role": intel_result.role,
            "seniority": intel_result.seniority,
            "location": intel_result.location,
            "skills": intel_result.skills
        },
        "signals": {
            "hiring_pressure": intel_result.hiring_pressure,
            "role_scarcity": intel_result.role_scarcity
        }
    }
    
    # Run orchestrator
    orchestrator = SearchOrchestrator()
    result = await orchestrator.orchestrate(query, intelligence_envelope)
    
    # Verify leads are enriched
    leads = result["leads"]
    assert len(leads) > 0
    
    for lead in leads:
        # Should have enriched fields
        assert "score" in lead, "Lead missing score field"
        assert "confidence" in lead, "Lead missing confidence field"
        assert "company" in lead or "company_name" in lead, "Lead missing company field"
        
        # Verify contract validation would pass
        clean = LeadContract.sanitize(lead)
        assert clean is not None, f"Lead failed contract validation: {lead}"
        assert LeadContract.validate_required(clean), f"Lead missing required fields: {clean}"
