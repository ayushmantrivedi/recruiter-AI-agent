
import pytest
from app.search.lead_scorer import LeadScorer
from app.search.lead_normalizer import NormalizedLead

@pytest.fixture
def mock_signals():
    return {
        "hiring_pressure": 0.8, # High pressure
        "role_scarcity": 0.6,
        "market_difficulty": 0.5
    }

def test_score_calculation(mock_signals):
    lead = NormalizedLead(
        company_name="Test", role="Dev", location="Remote", job_url="", source="", skills=[],
        hiring_urgency="High", # +15
        company_growth_stage="High Growth", # +10
        funding_stage="Series A", # +10
        salary_range="100k" # +10
    )
    # Base: 50
    # Signals: 0.8 * 20 = 16, 0.6 * 15 = 9.  Total Signal: 25
    # Attributes: 15 + 10 + 10 + 10 = 45
    # Total: 50 + 25 + 45 = 120 -> Cap 100
    
    score = LeadScorer.compute_score(lead, mock_signals)
    assert score == 100.0

def test_low_score_calculation(mock_signals):
    lead = NormalizedLead(
        company_name="Test", role="Dev", location="Remote", job_url="", source="", skills=[],
        hiring_urgency="Low", # +5
        company_growth_stage="Stable", # +5
        funding_stage="Unknown", # 0
        salary_range=None # 0
    )
    # Base: 50
    # Signals: 25
    # Attributes: 10
    # Total: 85
    
    score = LeadScorer.compute_score(lead, mock_signals)
    assert score == 85.0

def test_missing_signals():
    lead = NormalizedLead(company_name="T", role="R", location="L", job_url="", source="", skills=[])
    score = LeadScorer.compute_score(lead, {})
    # Base 50
    # Default signals: 0.5*20 + 0.5*15 = 10 + 7.5 = 17.5
    # Attributes: 0
    # Total: 67.5
    assert score == 67.5
