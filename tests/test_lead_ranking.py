
import pytest
from app.search.lead_ranker import LeadRanker
from app.search.lead_normalizer import NormalizedLead

def test_ranking_order():
    lead1 = NormalizedLead(company_name="A", role="Dev", location="Remote", job_url="", source="", skills=[], confidence_score=80.0)
    lead2 = NormalizedLead(company_name="B", role="Dev", location="Remote", job_url="", source="", skills=[], confidence_score=95.0)
    lead3 = NormalizedLead(company_name="C", role="Dev", location="Remote", job_url="", source="", skills=[], confidence_score=60.0)
    
    leads = [lead1, lead2, lead3]
    ranked = LeadRanker.rank(leads)
    
    assert ranked[0].confidence_score == 95.0
    assert ranked[0].company_name == "B"
    assert ranked[1].confidence_score == 80.0
    assert ranked[2].confidence_score == 60.0
