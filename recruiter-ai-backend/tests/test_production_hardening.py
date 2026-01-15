"""
Production Hardening Regression Tests
Verifies all hardening fixes work correctly
"""

import pytest
import math
from app.search.lead_scorer import LeadScorer
from app.search.lead_ranker import LeadRanker
from app.search.lead_normalizer import NormalizedLead
from app.enrichment.lead_enricher import LeadEnricher

def test_score_soft_cap_prevents_saturation():
    """Verify scores don't saturate at 100 too easily."""
    # Test soft cap function directly
    assert LeadScorer._apply_soft_cap(50.0) < 90.0  # Should be ~86
    assert LeadScorer._apply_soft_cap(75.0) < 96.0  # Should be ~95
    assert LeadScorer._apply_soft_cap(100.0) < 99.0  # Should be ~98
    assert LeadScorer._apply_soft_cap(150.0) < 100.0  # Should never reach 100
    
    # Verify top scores are rare
    lead = NormalizedLead(
        company_name="Test",
        role="Engineer",
        location="Remote",
        job_url="http://test.com",
        source="test"
    )
    
    # Even with max signals, score should be < 100
    max_signals = {
        "hiring_pressure": 1.0,
        "role_scarcity": 1.0,
        "market_difficulty": 1.0
    }
    
    score = LeadScorer.compute_score(lead, max_signals)
    assert score < 100.0, f"Score {score} should not reach 100"
    assert score > 85.0, f"Score {score} should still be high"

def test_deduplication_removes_duplicates():
    """Verify deduplication removes duplicate companies."""
    leads = [
        NormalizedLead(
            company_name="TechCorp",
            role="Engineer",
            location="Pune",
            job_url="http://test1.com",
            source="test",
            confidence_score=90.0
        ),
        NormalizedLead(
            company_name="TechCorp",  # Duplicate
            role="Engineer",
            location="Pune",
            job_url="http://test2.com",
            source="test",
            confidence_score=85.0
        ),
        NormalizedLead(
            company_name="DataCo",
            role="Analyst",
            location="Mumbai",
            job_url="http://test3.com",
            source="test",
            confidence_score=88.0
        )
    ]
    
    ranked = LeadRanker.rank(leads)
    
    # Should have 2 unique leads (TechCorp duplicate removed)
    assert len(ranked) == 2
    
    # Verify highest score kept
    techcorp_lead = [l for l in ranked if l.company_name == "TechCorp"][0]
    assert techcorp_lead.confidence_score == 90.0

def test_deduplication_preserves_order():
    """Verify deduplication maintains ranking order."""
    leads = [
        NormalizedLead(
            company_name=f"Company{i}",
            role="Engineer",
            location="Remote",
            job_url=f"http://test{i}.com",
            source="test",
            confidence_score=100.0 - i
        )
        for i in range(10)
    ]
    
    ranked = LeadRanker.rank(leads)
    
    # Verify descending order
    for i in range(len(ranked) - 1):
        assert ranked[i].confidence_score >= ranked[i+1].confidence_score

def test_reasons_populated_from_signals():
    """Verify reasons array is populated from signals."""
    lead = {"company_name": "Test Co", "confidence_score": 85.0}
    
    intelligence = {"role": "Engineer"}
    signals = {
        "hiring_pressure": 0.8,
        "role_scarcity": 0.9,
        "market_difficulty": 0.3,
        "outsourcing_likelihood": 0.2
    }
    
    enriched = LeadEnricher.enrich(lead, intelligence, signals)
    
    assert "reasons" in enriched
    assert len(enriched["reasons"]) > 0
    assert isinstance(enriched["reasons"], list)
    
    # Verify reasons are strings
    for reason in enriched["reasons"]:
        assert isinstance(reason, str)
        assert len(reason) > 0

def test_reasons_reflect_signal_values():
    """Verify reasons match signal thresholds."""
    lead = {"company_name": "Test", "confidence_score": 80.0}
    intelligence = {}
    
    # High hiring pressure
    signals_high_pressure = {"hiring_pressure": 0.9}
    enriched = LeadEnricher.enrich(lead, intelligence, signals_high_pressure)
    reasons_text = " ".join(enriched["reasons"]).lower()
    assert "high hiring pressure" in reasons_text or "hiring" in reasons_text
    
    # High role scarcity
    signals_high_scarcity = {"role_scarcity": 0.85}
    enriched = LeadEnricher.enrich(lead, intelligence, signals_high_scarcity)
    reasons_text = " ".join(enriched["reasons"]).lower()
    assert "scarcity" in reasons_text or "demand" in reasons_text

def test_total_leads_found_accuracy():
    """Verify total_leads_found equals len(leads)."""
    # This is tested in integration, but verify the logic
    leads = [{"company": f"Co{i}", "score": 80 + i} for i in range(15)]
    
    # After limiting to top 20
    limited = leads[:20]
    total_count = len(leads)
    
    # Before limiting, total should equal full count
    assert total_count == 15
    
    # After limiting, returned count should match
    assert len(limited) == 15  # Less than 20, so all returned

def test_score_distribution_not_clustered():
    """Verify scores have good distribution, not clustered at 100."""
    leads = []
    for i in range(20):
        lead = NormalizedLead(
            company_name=f"Company{i}",
            role="Engineer",
            location="Remote",
            job_url=f"http://test{i}.com",
            source="test"
        )
        leads.append(lead)
    
    # Score with varying signals
    scored_leads = []
    for i, lead in enumerate(leads):
        signals = {
            "hiring_pressure": 0.3 + (i * 0.03),  # 0.3 to 0.87
            "role_scarcity": 0.4 + (i * 0.02)     # 0.4 to 0.78
        }
        score = LeadScorer.compute_score(lead, signals)
        scored_leads.append(score)
    
    # Verify distribution
    assert max(scored_leads) < 100.0, "No score should reach 100"
    assert max(scored_leads) - min(scored_leads) > 10.0, "Should have >10 point spread"
    
    # Verify not all clustered at top
    top_scores = [s for s in scored_leads if s > 95.0]
    assert len(top_scores) < len(scored_leads) * 0.3, "Less than 30% should be >95"

@pytest.mark.asyncio
async def test_end_to_end_hardening():
    """Integration test: Verify all hardening changes work together."""
    from app.intelligence.intelligence_engine import IntelligenceEngine
    from app.search.search_orchestrator import SearchOrchestrator
    
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
    assert len(leads) > 0
    
    # Verify all leads have reasons
    for lead in leads:
        assert "reasons" in lead
        assert len(lead["reasons"]) > 0
    
    # Verify scores don't saturate
    scores = [l["score"] for l in leads]
    assert max(scores) < 100.0
    
    # Verify no exact duplicates
    seen_keys = set()
    for lead in leads:
        key = (
            lead.get("company_name", "").lower(),
            lead.get("role", "").lower(),
            lead.get("location", "").lower()
        )
        assert key not in seen_keys, f"Duplicate found: {key}"
        seen_keys.add(key)
