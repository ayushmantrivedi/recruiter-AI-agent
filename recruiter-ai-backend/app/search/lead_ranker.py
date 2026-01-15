from typing import List, Dict, Tuple
from .lead_normalizer import NormalizedLead
from ..utils.logger import get_logger

logger = get_logger("lead_ranker")

class LeadRanker:
    """Ranks and deduplicates normalized leads."""
    
    @staticmethod
    def rank(leads: List[NormalizedLead]) -> List[NormalizedLead]:
        """
        Sort leads by confidence score descending and deduplicate.
        Deduplication key: (company_name, role, location)
        Keeps highest scoring instance of each unique lead.
        """
        # First, sort by confidence score descending
        sorted_leads = sorted(leads, key=lambda x: x.confidence_score, reverse=True)
        
        # Deduplicate by (company, role, location)
        seen: Dict[Tuple[str, str, str], NormalizedLead] = {}
        deduplicated = []
        
        for lead in sorted_leads:
            # Create deduplication key
            key = (
                lead.company_name.lower().strip(),
                lead.role.lower().strip() if lead.role else "",
                lead.location.lower().strip() if lead.location else ""
            )
            
            # Keep first occurrence (highest score due to sorting)
            if key not in seen:
                seen[key] = lead
                deduplicated.append(lead)
        
        duplicates_removed = len(sorted_leads) - len(deduplicated)
        if duplicates_removed > 0:
            logger.info(f"Deduplication removed {duplicates_removed} duplicate leads")
        
        return deduplicated
