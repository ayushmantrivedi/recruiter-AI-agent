from typing import List
from .lead_normalizer import NormalizedLead

class LeadRanker:
    """Ranks normalized leads."""
    
    @staticmethod
    def rank(leads: List[NormalizedLead]) -> List[NormalizedLead]:
        """Sort leads by confidence score descending."""
        # Simple sorting for now, but could include diverse re-ranking later
        return sorted(leads, key=lambda x: x.confidence_score, reverse=True)
