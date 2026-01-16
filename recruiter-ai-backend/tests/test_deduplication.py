"""
Production Hardening Tests - Deduplication
Tests for lead deduplication logic and invariant enforcement
"""

import pytest
from app.search.lead_ranker import LeadRanker
from app.search.lead_normalizer import NormalizedLead


def test_deduplication_removes_exact_duplicates():
    """Verify exact duplicates are removed."""
    leads = [
        NormalizedLead(
            company_name="TechCorp",
            role="Engineer",
            location="Pune",
            job_url="http://test1.com",
            source="test",
            skills=[],
            confidence_score=90.0
        ),
        NormalizedLead(
            company_name="TechCorp",  # Exact duplicate
            role="Engineer",
            location="Pune",
            job_url="http://test2.com",  # Different URL
            source="test",
            skills=[],
            confidence_score=85.0
        ),
    ]
    
    ranked = LeadRanker.rank(leads)
    
    assert len(ranked) == 1, "Should have 1 unique lead"
    assert ranked[0].confidence_score == 90.0, "Should keep highest score"


def test_deduplication_preserves_highest_score():
    """Verify deduplication keeps highest scoring instance."""
    leads = [
        NormalizedLead(
            company_name="DataCo",
            role="Analyst",
            location="Mumbai",
            job_url="http://test1.com",
            source="test",
            skills=[],
            confidence_score=75.0
        ),
        NormalizedLead(
            company_name="DataCo",
            role="Analyst",
            location="Mumbai",
            job_url="http://test2.com",
            source="test",
            skills=[],
            confidence_score=92.0  # Higher score
        ),
        NormalizedLead(
            company_name="DataCo",
            role="Analyst",
            location="Mumbai",
            job_url="http://test3.com",
            source="test",
            skills=[],
            confidence_score=80.0
        ),
    ]
    
    ranked = LeadRanker.rank(leads)
    
    assert len(ranked) == 1
    assert ranked[0].confidence_score == 92.0


def test_deduplication_handles_case_insensitive():
    """Verify deduplication is case-insensitive."""
    leads = [
        NormalizedLead(
            company_name="TechCorp",
            role="Engineer",
            location="Remote",
            job_url="http://test1.com",
            source="test",
            skills=[],
            confidence_score=85.0
        ),
        NormalizedLead(
            company_name="TECHCORP",  # Different case
            role="ENGINEER",
            location="REMOTE",
            job_url="http://test2.com",
            source="test",
            skills=[],
            confidence_score=90.0
        ),
    ]
    
    ranked = LeadRanker.rank(leads)
    
    assert len(ranked) == 1, "Case-insensitive dedup should remove duplicate"


def test_deduplication_different_companies_preserved():
    """Verify different companies are not deduplicated."""
    leads = [
        NormalizedLead(
            company_name="TechCorp",
            role="Engineer",
            location="Pune",
            job_url="http://test1.com",
            source="test",
            skills=[],
            confidence_score=85.0
        ),
        NormalizedLead(
            company_name="DataCo",  # Different company
            role="Engineer",
            location="Pune",
            job_url="http://test2.com",
            source="test",
            skills=[],
            confidence_score=90.0
        ),
    ]
    
    ranked = LeadRanker.rank(leads)
    
    assert len(ranked) == 2, "Different companies should be preserved"


def test_deduplication_different_roles_preserved():
    """Verify same company with different roles are preserved."""
    leads = [
        NormalizedLead(
            company_name="TechCorp",
            role="Engineer",
            location="Pune",
            job_url="http://test1.com",
            source="test",
            skills=[],
            confidence_score=85.0
        ),
        NormalizedLead(
            company_name="TechCorp",
            role="Manager",  # Different role
            location="Pune",
            job_url="http://test2.com",
            source="test",
            skills=[],
            confidence_score=90.0
        ),
    ]
    
    ranked = LeadRanker.rank(leads)
    
    assert len(ranked) == 2, "Different roles should be preserved"


def test_deduplication_different_locations_preserved():
    """Verify same company/role with different locations are preserved."""
    leads = [
        NormalizedLead(
            company_name="TechCorp",
            role="Engineer",
            location="Pune",
            job_url="http://test1.com",
            source="test",
            skills=[],
            confidence_score=85.0
        ),
        NormalizedLead(
            company_name="TechCorp",
            role="Engineer",
            location="Mumbai",  # Different location
            job_url="http://test2.com",
            source="test",
            skills=[],
            confidence_score=90.0
        ),
    ]
    
    ranked = LeadRanker.rank(leads)
    
    assert len(ranked) == 2, "Different locations should be preserved"


def test_deduplication_handles_empty_list():
    """Verify deduplication handles empty input."""
    ranked = LeadRanker.rank([])
    assert ranked == []


def test_deduplication_handles_single_lead():
    """Verify deduplication handles single lead."""
    leads = [
        NormalizedLead(
            company_name="TechCorp",
            role="Engineer",
            location="Pune",
            job_url="http://test1.com",
            source="test",
            skills=[],
            confidence_score=85.0
        )
    ]
    
    ranked = LeadRanker.rank(leads)
    assert len(ranked) == 1
    assert ranked[0].company_name == "TechCorp"


def test_deduplication_skips_empty_company():
    """Verify leads with empty company names are skipped."""
    leads = [
        NormalizedLead(
            company_name="",  # Empty company
            role="Engineer",
            location="Pune",
            job_url="http://test1.com",
            source="test",
            skills=[],
            confidence_score=85.0
        ),
        NormalizedLead(
            company_name="TechCorp",
            role="Engineer",
            location="Pune",
            job_url="http://test2.com",
            source="test",
            skills=[],
            confidence_score=90.0
        ),
    ]
    
    ranked = LeadRanker.rank(leads)
    
    assert len(ranked) == 1
    assert ranked[0].company_name == "TechCorp"


def test_deduplication_maintains_sort_order():
    """Verify deduplication maintains descending score order."""
    leads = [
        NormalizedLead(
            company_name=f"Company{i}",
            role="Engineer",
            location="Remote",
            job_url=f"http://test{i}.com",
            source="test",
            skills=[],
            confidence_score=100.0 - i
        )
        for i in range(10)
    ]
    
    ranked = LeadRanker.rank(leads)
    
    # Verify descending order
    for i in range(len(ranked) - 1):
        assert ranked[i].confidence_score >= ranked[i+1].confidence_score
