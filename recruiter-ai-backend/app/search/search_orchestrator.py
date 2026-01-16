import asyncio
from typing import List, Dict, Any
from ..utils.logger import get_logger
from .data_sources import MockJobBoard, MockStartupDB, MockCompanyAPI
from .lead_normalizer import LeadNormalizer
from .lead_scorer import LeadScorer
from .lead_ranker import LeadRanker

logger = get_logger("search_orchestrator")

from dataclasses import dataclass, field
import time

@dataclass
class OrchestrationSummary:
    """Detailed metrics for the search execution."""
    query: str
    execution_mode: str
    total_duration_ms: float = 0.0
    
    # Provider Metrics
    providers_called: int = 0
    providers_succeeded: int = 0
    providers_failed: int = 0
    provider_diagnostics: Dict[str, Any] = field(default_factory=dict)
    
    # Lead Fidelity
    total_raw_leads: int = 0
    total_normalized_leads: int = 0
    total_scored_leads: int = 0
    total_ranked_leads: int = 0
    total_leads_found: int = 0 # Contract: Pre-truncation count
    
    # Dedup Metrics
    duplicates_removed: int = 0
    duplicate_rate: float = 0.0

class SearchOrchestrator:
    """Orchestrates the search, normalization, scoring, and ranking process."""
    
    def __init__(self):
        from ..config import settings, ExecutionMode
        self.mode = settings.logging.mode
        self.sources = []
        
        self.sources = []
        
        # 1. Public APIs (ArbeitNow, GitHub, etc.)
        # These are "Real" APIs wrapped by MockJobBoard (legacy name, should be PublicJobProvider)
        if settings.agent.enable_arbeitnow or settings.agent.enable_github_jobs:
            logger.info("Public APIs ENABLED", arbeitnow=settings.agent.enable_arbeitnow, github=settings.agent.enable_github_jobs)
            from .data_sources import MockJobBoard
            self.sources.append(MockJobBoard())
            
        # 2. Mock Data (Fake/Static)
        if settings.agent.enable_mock_sources:
            logger.info("Mock Data Sources ENABLED")
            from .data_sources import MockStartupDB, MockCompanyAPI
            self.sources.extend([
                MockStartupDB(),
                MockCompanyAPI()
            ])
            
        self.validate_active_providers()
        
        self.normalizer = LeadNormalizer()
        self.scorer = LeadScorer()
        self.ranker = LeadRanker()

    def validate_active_providers(self):
        """Fail fast if no providers are enabled."""
        if not self.sources:
            error_msg = "CRITICAL: No search providers enabled! Check SEARCH_MODE and ENABLE_ flags."
            logger.critical(error_msg)
            raise RuntimeError(error_msg)
        logger.info(f"SearchOrchestrator initialized with {len(self.sources)} providers", 
                    providers=[s.__class__.__name__ for s in self.sources])

    async def orchestrate(self, query: str, intelligence_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full search pipeline execution with observability.
        """
        start_time = time.time()
        
        # Init Summary
        summary = OrchestrationSummary(
            query=query,
            execution_mode=self.mode.value
        )
        
        logger.info("Starting Search Orchestration", query=query, mode=summary.execution_mode)
        
        # 1. Prepare Constraints
        metadata = intelligence_data.get("intelligence", {})
        signals = intelligence_data.get("signals", {})
        
        constraints = {
            "role": metadata.get("role", query),
            "location": metadata.get("location") or "Remote",
            "skills": metadata.get("skills", []),
            "seniority": metadata.get("seniority", "")
        }
        
        # 2. Parallel Fetch with Telemetry
        summary.providers_called = len(self.sources)
        provider_telemetry = {}
        
        async def fetch_with_telemetry(source):
            name = source.__class__.__name__
            t0 = time.time()
            try:
                leads = await source.fetch(query, constraints)
                dt = (time.time() - t0) * 1000
                provider_telemetry[name] = {
                    "status": "success",
                    "latency_ms": round(dt, 2),
                    "leads_found": len(leads)
                }
                summary.providers_succeeded += 1
                return leads
            except Exception as e:
                dt = (time.time() - t0) * 1000
                provider_telemetry[name] = {
                    "status": "error",
                    "latency_ms": round(dt, 2),
                    "error": str(e)
                }
                summary.providers_failed += 1
                return e

        fetch_tasks = [fetch_with_telemetry(source) for source in self.sources]
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        
        raw_leads = []
        for res in results:
            if isinstance(res, list):
                raw_leads.extend(res)
            elif isinstance(res, Exception):
                logger.error(f"Source fetch failed: {res}")
        
        summary.total_raw_leads = len(raw_leads)
        summary.provider_diagnostics = provider_telemetry
        
        logger.info(f"Fetched {len(raw_leads)} raw leads", telemetry=provider_telemetry)
        
        # Health Check
        if not raw_leads:
             logger.critical("HEALTH CHECK FAILED: 0 leads fetched", telemetry=provider_telemetry)
        
        # 3. Normalize
        normalized_leads = self.normalizer.batch_normalize(raw_leads)
        summary.total_normalized_leads = len(normalized_leads)
        
        # 4. Score
        scored_leads = self.scorer.score_leads(normalized_leads, signals)
        summary.total_scored_leads = len(scored_leads)
        
        # 5. Rank
        ranked_leads = self.ranker.rank(scored_leads)
        summary.total_ranked_leads = len(ranked_leads)
        
        # Metrics
        summary.duplicates_removed = len(scored_leads) - len(ranked_leads)
        summary.duplicate_rate = round(summary.duplicates_removed / len(scored_leads), 3) if scored_leads else 0.0
        
        # 6. Enrich
        from ..enrichment.lead_enricher import LeadEnricher
        lead_dicts = [lead.to_dict() for lead in ranked_leads]
        enriched_leads = LeadEnricher.enrich_batch(lead_dicts, metadata, signals)
        
        # 7. Finalize
        summary.total_leads_found = len(enriched_leads) # Pre-truncation count
        summary.total_duration_ms = round((time.time() - start_time) * 1000, 2)
        
        # Validation
        if summary.total_leads_found < len(enriched_leads):
             # Should be impossible if set above, but kept for sanity
             summary.total_leads_found = len(enriched_leads)

        return {
            "leads": enriched_leads,
            "total_count": summary.total_leads_found,
            "evidence_objects": enriched_leads,
            "top_companies": list(set(l.get("company_name", "Unknown") for l in enriched_leads[:5])),
            "metrics": {
                "raw_leads_fetched": summary.total_raw_leads,
                "normalized_leads": summary.total_normalized_leads,
                "scored_leads": summary.total_scored_leads,
                "unique_leads": summary.total_ranked_leads,
                "duplicates_removed": summary.duplicates_removed,
                "duplicate_rate": summary.duplicate_rate,
                "provider_diagnostics": summary.provider_diagnostics
            },
            "orchestration_summary": summary.__dict__
        }

# Global instance
search_orchestrator = SearchOrchestrator()
