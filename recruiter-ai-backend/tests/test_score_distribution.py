"""
Production Hardening Tests - Score Distribution
Tests for score variance, spread enforcement, and confidence scaling
"""

import pytest
import statistics
from app.search.lead_scorer import LeadScorer
from app.search.lead_normalizer import NormalizedLead
from app.enrichment.lead_enricher import LeadEnricher


def test_score_range_enforcement():
    """Verify scores are clamped between 40 and 100."""
    # Create a dummy lead
    lead = NormalizedLead(
        company_name="Test", role="Eng", location="Remote", job_url="http://test.com", source="test", skills=[]
    )
    
    # Test Max (All perfect)
    lead.hiring_urgency = "High"
    lead.company_growth_stage = "High Growth"
    lead.funding_stage = "Series C"
    lead.salary_range = "Yes"
    lead.skills = ["a","b","c","d","e"]
    
    max_signals = {"hiring_pressure": 1.0, "role_scarcity": 1.0, "market_difficulty": 0.0}
    max_s = LeadScorer.compute_score(lead, max_signals)
    assert max_s <= 100.0, f"Max score {max_s} exceeded 100"
    
    # Test Min (All terrible)
    lead.hiring_urgency = "Unknown"
    lead.company_growth_stage = "Unknown" 
    lead.funding_stage = "Unknown"
    lead.salary_range = None
    lead.skills = []
    
    min_signals = {"hiring_pressure": 0.0, "role_scarcity": 0.0, "market_difficulty": 1.0}
    min_s = LeadScorer.compute_score(lead, min_signals)
    assert min_s >= 40.0, f"Min score {min_s} went below 40"


def test_score_variance_with_different_signals():
    """Verify scores vary with different signal combinations."""
    lead = NormalizedLead(
        company_name="Test",
        role="Engineer",
        location="Remote",
        job_url="http://test.com",
        source="test",
        skills=[]
    )
    
    # Low signals
    low_signals = {
        "hiring_pressure": 0.2,
        "role_scarcity": 0.3,
        "market_difficulty": 0.8
    }
    low_score = LeadScorer.compute_score(lead, low_signals)
    
    # High signals
    high_signals = {
        "hiring_pressure": 0.9,
        "role_scarcity": 0.85,
        "market_difficulty": 0.2
    }
    # Add attributes for the high case to show true separation
    lead.hiring_urgency = "High"
    lead.company_growth_stage = "High Growth"
    lead.funding_stage = "Series C"
    lead.salary_range = "$200k"
    lead.skills = ["Python", "AWS", "K8s"]
    
    high_score = LeadScorer.compute_score(lead, high_signals)
    
    # Verify significant difference implies we need > 30 points gap now
    assert high_score > low_score + 30, f"High score ({high_score}) should be >30 points higher than low score ({low_score})"
    assert low_score < 50, f"Low score ({low_score}) should be < 50"
    assert high_score > 80, f"High score ({high_score}) should be > 80"
    
    
def test_score_distribution_has_spread():
    """Verify score distribution has good spread across leads."""
    leads = []
    for i in range(20):
        lead = NormalizedLead(
            company_name=f"Company{i}",
            role="Engineer",
            location="Remote",
            job_url=f"http://test{i}.com",
            source="test",
            skills=[],
            # Give them a baseline so they aren't all stuck at 40
            hiring_urgency="Medium",
            company_growth_stage="Stable", 
            funding_stage="Series B",
            salary_range="Yes" # 5 points
        )
        leads.append(lead)
    
    # Score with varying signals
    scored_leads = []
    scores = []
    for i, lead in enumerate(leads):
        signals = {
            "hiring_pressure": 0.3 + (i * 0.03),  # 0.3 to 0.87
            "role_scarcity": 0.4 + (i * 0.02),     # 0.4 to 0.78
            "market_difficulty": 0.5
        }
        s = LeadScorer.compute_score(lead, signals)
        lead.confidence_score = s
        scored_leads.append(lead)
        scores.append(s)
    
    # Verify distribution
    assert max(scores) <= 100.0, "No score should reach >100"
    assert max(scores) - min(scores) > 10.0, "Should have >10 point spread"
    


def test_score_no_clustering_at_top():
    """Verify scores don't cluster near 100 (variance check)."""
    leads = []
    # Create leads with slight variations, all "good" but not identical
    for i in range(30):
        lead = NormalizedLead(
            company_name=f"Company{i}",
            role="Engineer",
            location="Remote",
            job_url=f"http://test{i}.com",
            source="test",
            skills=["Python", "AWS"],
            # Vary attributes slightly
            hiring_urgency="High" if i % 2 == 0 else "Medium",
            company_growth_stage="High Growth" if i % 3 == 0 else "Stable",
            funding_stage="Series A" if i % 4 == 0 else "Series B",
            salary_range="$150k-$200k"
        )
        leads.append(lead)
    
    # Score all with high signals
    max_signals = {
        "hiring_pressure": 0.95,
        "role_scarcity": 0.9,
        "market_difficulty": 0.2
    }
    
    for lead in leads:
        lead.confidence_score = LeadScorer.compute_score(lead, max_signals)
        
    scores = [l.confidence_score for l in leads]
    
    # Should see spread
    assert max(scores) <= 100.0, "Max score should be <= 100"
    assert min(scores) >= 40.0, "Min score should be >= 40 (base floor)"
    
    # Verify standard deviation > 10 as requested
    import statistics
    std_dev = statistics.stdev(scores)
    assert std_dev > 10.0, f"Standard deviation {std_dev} should be > 10.0"


def test_confidence_realistic_range():
    """Verify confidence values are in realistic 0.4-0.95 range."""
    # Low score
    low_lead = {"confidence_score": 30.0, "source": "unknown"}
    low_enriched = LeadEnricher.enrich(low_lead, {}, {})
    assert 0.4 <= low_enriched["confidence"] <= 0.6, f"Low confidence ({low_enriched['confidence']}) should be 0.4-0.6"
    
    # Medium score
    med_lead = {"confidence_score": 60.0, "source": "job_board"}
    med_enriched = LeadEnricher.enrich(med_lead, {}, {})
    assert 0.6 <= med_enriched["confidence"] <= 0.8, f"Medium confidence ({med_enriched['confidence']}) should be 0.6-0.8"
    
    # High score
    high_lead = {"confidence_score": 90.0, "source": "company_api"}
    high_enriched = LeadEnricher.enrich(high_lead, {}, {})
    assert 0.8 <= high_enriched["confidence"] <= 0.95, f"High confidence ({high_enriched['confidence']}) should be 0.8-0.95"


def test_confidence_never_exceeds_95():
    """Verify confidence is capped at 0.95."""
    # Even with perfect score and max evidence
    perfect_lead = {
        "confidence_score": 100.0,
        "source": "company_api",
        "evidence_count": 100
    }
    enriched = LeadEnricher.enrich(perfect_lead, {}, {})
    assert enriched["confidence"] <= 0.95, f"Confidence ({enriched['confidence']}) should never exceed 0.95"


def test_confidence_never_below_40():
    """Verify confidence has floor at 0.4."""
    # Even with zero score and unknown source
    zero_lead = {
        "confidence_score": 0.0,
        "source": "unknown",
        "evidence_count": 0
    }
    enriched = LeadEnricher.enrich(zero_lead, {}, {})
    assert enriched["confidence"] >= 0.4, f"Confidence ({enriched['confidence']}) should never be below 0.4"


def test_confidence_evidence_boost():
    """Verify evidence count increases confidence."""
    base_lead = {"confidence_score": 70.0, "source": "job_board", "evidence_count": 0}
    base_enriched = LeadEnricher.enrich(base_lead, {}, {})
    base_confidence = base_enriched["confidence"]
    
    evidence_lead = {"confidence_score": 70.0, "source": "job_board", "evidence_count": 5}
    evidence_enriched = LeadEnricher.enrich(evidence_lead, {}, {})
    evidence_confidence = evidence_enriched["confidence"]
    
    assert evidence_confidence > base_confidence, "More evidence should increase confidence"
    assert evidence_confidence - base_confidence <= 0.05, "Evidence boost should be <= 0.05"


def test_confidence_source_reliability():
    """Verify source reliability affects confidence."""
    score = 70.0
    
    # Unknown source (penalty)
    unknown_lead = {"confidence_score": score, "source": "unknown"}
    unknown_enriched = LeadEnricher.enrich(unknown_lead, {}, {})
    
    # Job board (baseline)
    job_lead = {"confidence_score": score, "source": "job_board"}
    job_enriched = LeadEnricher.enrich(job_lead, {}, {})
    
    # Company API (boost)
    company_lead = {"confidence_score": score, "source": "company_api"}
    company_enriched = LeadEnricher.enrich(company_lead, {}, {})
    
    assert unknown_enriched["confidence"] < job_enriched["confidence"]
    assert company_enriched["confidence"] > job_enriched["confidence"]


def test_score_distribution_validation_warning():
    """Verify low variance triggers warning (doesn't fail)."""
    # Create leads with very similar scores
    leads = [
        NormalizedLead(
            company_name=f"Company{i}",
            role="Engineer",
            location="Remote",
            job_url=f"http://test{i}.com",
            source="test",
            skills=[],
            confidence_score=80.0 + (i * 0.1)  # Very small variance
        )
        for i in range(10)
    ]
    
    # Should not crash, just log warning
    signals = {"hiring_pressure": 0.5, "role_scarcity": 0.5}
    scored = LeadScorer.score_leads(leads, signals)
    
    assert len(scored) == 10, "Should process all leads despite low variance"
