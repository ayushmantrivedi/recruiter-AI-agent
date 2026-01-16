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
        if not leads:
            return []
        
        # First, sort by confidence score descending
        sorted_leads = sorted(leads, key=lambda x: x.confidence_score, reverse=True)
        
        # Deduplicate by (company, role, location)
        seen: Dict[Tuple[str, str, str], NormalizedLead] = {}
        deduplicated = []
        
        for lead in sorted_leads:
            # Create deduplication key with safe handling of missing fields
            # Use empty string as default for missing role/location
            company_key = lead.company_name.lower().strip() if lead.company_name else ""
            role_key = lead.role.lower().strip() if hasattr(lead, 'role') and lead.role else ""
            location_key = lead.location.lower().strip() if hasattr(lead, 'location') and lead.location else ""
            
            key = (company_key, role_key, location_key)
            
            # Skip if company is empty (invalid lead)
            if not company_key:
                logger.warning("Skipping lead with empty company name during deduplication")
                continue
            
            # Keep first occurrence (highest score due to sorting)
            if key not in seen:
                seen[key] = lead
                deduplicated.append(lead)
        
        duplicates_removed = len(sorted_leads) - len(deduplicated)
        if duplicates_removed > 0:
            logger.info(f"Deduplication removed {duplicates_removed} duplicate leads",
                       original_count=len(sorted_leads),
                       unique_count=len(deduplicated))
        
        # Invariant check: Ensure no duplicates in output
        dedup_keys = set()
        for lead in deduplicated:
            company_key = lead.company_name.lower().strip() if lead.company_name else ""
            role_key = lead.role.lower().strip() if hasattr(lead, 'role') and lead.role else ""
            location_key = lead.location.lower().strip() if hasattr(lead, 'location') and lead.location else ""
            key = (company_key, role_key, location_key)
            
            if key in dedup_keys:
                logger.error("INVARIANT VIOLATION: Duplicate found in deduplicated output",
                           company=lead.company_name,
                           role=getattr(lead, 'role', 'N/A'),
                           location=getattr(lead, 'location', 'N/A'))
            dedup_keys.add(key)
        
        return deduplicated
