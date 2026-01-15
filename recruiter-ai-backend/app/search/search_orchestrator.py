import asyncio
from typing import List, Dict, Any
from ..utils.logger import get_logger
from .data_sources import MockJobBoard, MockStartupDB, MockCompanyAPI
from .lead_normalizer import LeadNormalizer
from .lead_scorer import LeadScorer
from .lead_ranker import LeadRanker

logger = get_logger("search_orchestrator")

class SearchOrchestrator:
    """Orchestrates the search, normalization, scoring, and ranking process."""
    
    def __init__(self):
        self.sources = [
            MockJobBoard(),
            MockStartupDB(),
            MockCompanyAPI()
        ]
        self.normalizer = LeadNormalizer()
        self.scorer = LeadScorer()
        self.ranker = LeadRanker()

    async def orchestrate(self, query: str, intelligence_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full search pipeline execution.
        query: Original user query
        intelligence_data: Dict containing 'intelligence' (metadata) and 'signals' (metrics)
        """
        logger.info("Starting Search Orchestration", query=query)
        
        # 1. Prepare Constraints from Intelligence
        metadata = intelligence_data.get("intelligence", {})
        signals = intelligence_data.get("signals", {})
        
        constraints = {
            "role": metadata.get("role", query), # Fallback to query if role extraction failed
            "location": metadata.get("location") or "Remote", # STRICT: Use intelligence first, fallback only if null/empty
            "skills": metadata.get("skills", []),
            "seniority": metadata.get("seniority", "")
        }
        
        # 2. Parallel Fetch from Data Sources
        fetch_tasks = [source.fetch(query, constraints) for source in self.sources]
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        
        raw_leads = []
        for res in results:
            if isinstance(res, list):
                raw_leads.extend(res)
            elif isinstance(res, Exception):
                logger.error(f"Source fetch failed: {res}")
        
        logger.info(f"Fetched {len(raw_leads)} raw leads")
        
        # 3. Normalize
        normalized_leads = self.normalizer.batch_normalize(raw_leads)
        
        # 4. Score
        scored_leads = self.scorer.score_leads(normalized_leads, signals)
        
        # 5. Rank
        ranked_leads = self.ranker.rank(scored_leads)
        
        # 6. Enrich - Inject intelligence and scoring data into lead dicts
        from ..enrichment.lead_enricher import LeadEnricher
        lead_dicts = [lead.to_dict() for lead in ranked_leads]
        enriched_leads = LeadEnricher.enrich_batch(lead_dicts, metadata, signals)
        
        # 7. Format Output (similar to legacy 'evidence_objects' + 'ranked_leads')
        
        # Create legacy-compatible evidence list
        evidence_objects = enriched_leads  # Already dicts
        
        return {
            "leads": enriched_leads,
            "total_count": len(enriched_leads),
            "evidence_objects": evidence_objects, # Backward compat
            "top_companies": list(set(l.get("company_name", "Unknown") for l in enriched_leads[:5]))
        }

# Global instance
search_orchestrator = SearchOrchestrator()
