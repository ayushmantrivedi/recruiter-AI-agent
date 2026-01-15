from typing import Dict, Any
from .lead_normalizer import NormalizedLead
from ..utils.logger import get_logger

logger = get_logger("search.lead_scorer")

class LeadScorer:
    """Scores leads based on intelligence signals and lead attributes."""
    
    @staticmethod
    def compute_score(lead: NormalizedLead, signals: Dict[str, float]) -> float:
        """
        Compute a score between 0 and 100.
        Signals: hiring_pressure, role_scarcity, market_difficulty (0-1 floats)
        """
        base_score = 50.0
        
        # 1. Intelligence Signal Impact
        # High hiring pressure -> +score
        base_score += signals.get("hiring_pressure", 0.5) * 20 
        
        # High role scarcity -> -score (harder to convert, maybe? Or +score because valuable? 
        # Usually for a recruiter finding leads, high scarcity means 'hard to find', 
        # but if we FOUND one, it's a high value lead. Let's assume high score = high value lead.)
        base_score += signals.get("role_scarcity", 0.5) * 15
        
        # 2. Lead Attribute Impact
        # Urgency
        urgency_map = {"High": 15, "Medium": 10, "Low": 5, "Unknown": 0}
        base_score += urgency_map.get(lead.hiring_urgency, 0)
        
        # Growth Stage
        growth_map = {"High Growth": 10, "Stable": 5, "Early": 5, "Unknown": 0}
        base_score += growth_map.get(lead.company_growth_stage, 0)
        
        # Funding
        funding_map = {"Series A": 10, "Series B": 8, "Seed": 5, "Unknown": 0}
        base_score += funding_map.get(lead.funding_stage, 0)
        
        # Salary Presence (Recruiters love salary info)
        if lead.salary_range:
            base_score += 10
            
        # Cap at 100
        final_score = min(100.0, max(0.0, base_score))
        
        return round(final_score, 1)

    @staticmethod
    def score_leads(leads: list[NormalizedLead], signals: Dict[str, float]) -> list[NormalizedLead]:
        for lead in leads:
            lead.confidence_score = LeadScorer.compute_score(lead, signals)
        return leads
