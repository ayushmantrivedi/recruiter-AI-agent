from typing import Dict, Any
import math
from .lead_normalizer import NormalizedLead
from ..utils.logger import get_logger

logger = get_logger("search.lead_scorer")

class LeadScorer:
    """Scores leads based on intelligence signals and lead attributes."""
    
    @staticmethod
    def _apply_soft_cap(raw_score: float, max_score: float = 100.0) -> float:
        """
        Apply soft cap using tanh to prevent saturation.
        Maps [0, inf) -> [0, max_score) with diminishing returns.
        """
        # Normalize to [0, 1] range using tanh
        # tanh(x/30) gives smooth curve: 50->0.86, 75->0.95, 100->0.98
        normalized = math.tanh(raw_score / 30.0)
        return normalized * max_score
    
    @staticmethod
    def compute_score(lead: NormalizedLead, signals: Dict[str, float]) -> float:
        """
        Compute a score between 0 and 100 with soft cap to prevent saturation.
        Signals: hiring_pressure, role_scarcity, market_difficulty (0-1 floats)
        """
        base_score = 50.0
        
        # 1. Intelligence Signal Impact
        # High hiring pressure -> +score
        base_score += signals.get("hiring_pressure", 0.5) * 20 
        
        # High role scarcity -> +score (valuable lead)
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
            
        # Apply soft cap to prevent saturation
        final_score = LeadScorer._apply_soft_cap(base_score)
        
        return round(final_score, 1)

    @staticmethod
    def score_leads(leads: list[NormalizedLead], signals: Dict[str, float]) -> list[NormalizedLead]:
        for lead in leads:
            lead.confidence_score = LeadScorer.compute_score(lead, signals)
        return leads
