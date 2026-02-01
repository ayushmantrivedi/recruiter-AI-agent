import asyncio
from typing import List, Dict, Any
from ..utils.logger import get_logger
from .data_sources import MockJobBoard, MockCompanyAPI
from .lead_normalizer import LeadNormalizer
from .lead_scorer import LeadScorer
from .lead_ranker import LeadRanker

logger = get_logger("search_orchestrator")

from dataclasses import dataclass, field
import time

@dataclass
class ExecutionReport:
    """Canonical execution report for search orchestration."""
    query: str
    execution_mode: str
    execution_time_ms: float = 0.0
    
    # Provider Metrics
    providers_called: int = 0
    providers_succeeded: int = 0
    providers_failed: int = 0
    provider_diagnostics: Dict[str, Any] = field(default_factory=dict)
    
    # Lead Fidelity
    raw_leads_found: int = 0
    normalized_leads: int = 0
    ranked_leads_count: int = 0
    deduplicated_count: int = 0
    skipped_invalid_count: int = 0
    
    # Pipeline placeholders (filled later)
    leads_saved: int = 0
    query_id: str = "" # To be filled by pipeline

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
            
        # 2. Real-Time Web Scraper (Combined with Primary Sources)
        if settings.agent.enable_web_scraper:
            logger.info("Real-Time Web Scraper ENABLED (DuckDuckGo/LinkedIn/Indeed)")
            from .data_sources import RealTimeWebScraper
            self.sources.append(RealTimeWebScraper())

        # 3. Mock Data (Fake/Static) - Only if explicitly enabled
        if settings.agent.enable_mock_sources:
            logger.info("Mock Data Sources ENABLED")
            from .data_sources import MockCompanyAPI
            self.sources.extend([
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
        
        # Init Report
        report = ExecutionReport(
            query=query,
            execution_mode=self.mode.value
        )
        
        logger.info("Starting Search Orchestration", query=query, mode=report.execution_mode)
        
        # 1. LLM Query Parsing (Ear) - Extract structured search terms
        from ..intelligence.query_parser import query_parser
        parsed_query = await query_parser.parse(query)
        
        logger.info(f"Query parsed: {query}, Role: {parsed_query.get('role')}")
        
        # 2. Prepare Constraints from parsed query + intelligence data
        metadata = intelligence_data.get("intelligence", {})
        signals = intelligence_data.get("signals", {})
        
        # Prefer LLM-parsed values, fall back to intelligence metadata
        constraints = {
            "role": parsed_query.get("role") or metadata.get("role", query),
            "location": parsed_query.get("location") or metadata.get("location") or "Remote",
            "skills": parsed_query.get("skills") or metadata.get("skills", []),
            "seniority": metadata.get("seniority", ""),
            "keywords": parsed_query.get("keywords", [])  # New: LLM-extracted keywords
        }
        
        # 2. Parallel Fetch with Telemetry
        report.providers_called = len(self.sources)
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
                report.providers_succeeded += 1
                return leads
            except Exception as e:
                dt = (time.time() - t0) * 1000
                provider_telemetry[name] = {
                    "status": "error",
                    "latency_ms": round(dt, 2),
                    "error": str(e)
                }
                report.providers_failed += 1
                return e

        fetch_tasks = [fetch_with_telemetry(source) for source in self.sources]
        results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
        
        raw_leads = []
        for res in results:
            if isinstance(res, list):
                raw_leads.extend(res)
            elif isinstance(res, Exception):
                logger.error(f"Source fetch failed: {res}")
        
        report.raw_leads_found = len(raw_leads)
        report.provider_diagnostics = provider_telemetry
        
        logger.info(f"Fetched {len(raw_leads)} raw leads", telemetry=provider_telemetry)
        
        # Health Check
        if not raw_leads:
             logger.critical("HEALTH CHECK FAILED: 0 leads fetched", telemetry=provider_telemetry)
        
        # 3. Normalize
        normalized_leads = self.normalizer.batch_normalize(raw_leads)
        report.normalized_leads = len(normalized_leads)
        
        # 4. Score
        scored_leads = self.scorer.score_leads(normalized_leads, signals)
        
        # 5. Rank
        ranked_leads = self.ranker.rank(scored_leads)
        report.ranked_leads_count = len(ranked_leads)
        
        # Metrics
        report.deduplicated_count = len(scored_leads) - len(ranked_leads)
        
        # 6. Enrich
        from ..enrichment.lead_enricher import LeadEnricher
        lead_dicts = [lead.to_dict() for lead in ranked_leads]
        enriched_leads = LeadEnricher.enrich_batch(lead_dicts, metadata, signals)
        
        # 7. Finalize
        report.execution_time_ms = round((time.time() - start_time) * 1000, 2)
        
        return {
            "leads": enriched_leads,
            "total_count": report.raw_leads_found, # CORRECT: Use raw count for total found
            "evidence_objects": enriched_leads,
            "top_companies": list(set(l.get("company_name", "Unknown") for l in enriched_leads[:5])),
            "execution_report": report, # Pass the object for pipeline to use
            # Legacy/Observability Dict
            "orchestration_summary": report.__dict__
        }

# Global instance
search_orchestrator = SearchOrchestrator()
