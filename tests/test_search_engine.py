
import pytest
from app.search.lead_normalizer import LeadNormalizer, NormalizedLead

def test_lead_normalization_defaults():
    raw_data = {"company": "Test Corp", "title": "Dev"}
    normalized = LeadNormalizer.normalize(raw_data)
    assert normalized.company_name == "Test Corp"
    assert normalized.role == "Dev"
    assert normalized.location == "Remote" # Default
    assert normalized.hiring_urgency == "Unknown"

def test_lead_normalization_with_all_fields():
    raw_data = {
        "company": "Test Corp",
        "title": "Dev",
        "location": "Berlin",
        "url": "http://test.com",
        "skills": ["Python", "AI"],
        "salary_range": "100k",
        "hiring_urgency": "High",
        "growth_stage": "Stable",
        "funding": "Series A"
    }
    normalized = LeadNormalizer.normalize(raw_data)
    assert normalized.location == "Berlin"
    assert normalized.salary_range == "100k"
    assert normalized.hiring_urgency == "High"
    assert "Python" in normalized.skills

def test_lead_normalization_inference():
    raw_data = {
        "company": "Test Corp",
        "title": "Dev",
        "description": "We need someone asap for this urgent role"
    }
    normalized = LeadNormalizer.normalize(raw_data)
    assert normalized.hiring_urgency == "High"
