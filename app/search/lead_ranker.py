from typing import List, Dict, Tuple
from .lead_normalizer import NormalizedLead
from ..utils.logger import get_logger

logger = get_logger("lead_ranker")

class LeadRanker:
    """Ranks and deduplicates normalized leads."""
    
    @staticmethod
    def rank(leads: List[NormalizedLead]) -> List[NormalizedLead]:
        """
        Ranks leads by score and enforces quality invariants:
        1. Semantic Deduplication (Company + Normalized Role + Location)
        2. Result Density Control (Max 3 leads per company)
        """
        if not leads:
            return []
        
        # Constants
        MAX_LEADS_PER_COMPANY = 3
        
        # 1. Sort by confidence score descending
        sorted_leads = sorted(leads, key=lambda x: x.confidence_score, reverse=True)
        
        # 2. Group by company and deduplicate semantically
        company_buckets: Dict[str, List[NormalizedLead]] = {}
        seen_keys = set()
        
        deduplicated_count = 0
        
        for lead in sorted_leads:
            # Normalize keys for grouping
            company_key = lead.company_name.lower().strip()
            
            # Create a semantic role key: "Python Developer" == "Python Dev" (approx)
            # We strip common tech suffixes for the comparison key
            role_key = lead.role.lower().strip()
            role_key = role_key.replace("developer", "dev").replace("engineer", "eng")
            
            location_key = lead.location.lower().strip()
            
            # Intra-company duplicate key
            identity_key = (company_key, role_key, location_key)
            
            if identity_key in seen_keys:
                deduplicated_count += 1
                continue
            
            seen_keys.add(identity_key)
            
            # Ad to company bucket
            if company_key not in company_buckets:
                company_buckets[company_key] = []
            
            # Apply density limit
            if len(company_buckets[company_key]) < MAX_LEADS_PER_COMPANY:
                company_buckets[company_key].append(lead)
            else:
                # Discard as density overflow
                continue
                
        # 3. Re-assemble and re-sort (maintains overall score order)
        final_leads = []
        for bucket in company_buckets.values():
            final_leads.extend(bucket)
            
        final_leads = sorted(final_leads, key=lambda x: x.confidence_score, reverse=True)
        
        logger.info(f"Deduplication & Density Check complete", 
                   original=len(leads), 
                   final=len(final_leads),
                   semantic_duplicates=deduplicated_count)
        
        return final_leads
