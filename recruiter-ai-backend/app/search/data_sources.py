import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..apis.job_apis import job_api_manager
from ..utils.logger import get_logger

logger = get_logger("search.data_sources")

class DataSource(ABC):
    """Abstract base class for all data sources."""
    
    @abstractmethod
    async def fetch(self, query: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch data from the source."""
        pass

class MockJobBoard(DataSource):
    """Simulates a job board aggregator (wrapping actual JobAPIManager)."""
    
    def __init__(self):
        from ..config import settings
        self.timeout = settings.agent.external_api_timeout
        self.circuit_breaker_threshold = settings.agent.external_api_circuit_breaker_threshold
        self.enable_github_jobs = settings.agent.enable_github_jobs
        self.failure_count = 0
    
    async def fetch(self, query: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info(f"Fetching from MockJobBoard: {query}")
        
        # Circuit breaker check
        if self.failure_count >= self.circuit_breaker_threshold:
            logger.warning("Circuit breaker OPEN for MockJobBoard - skipping API call",
                         failure_count=self.failure_count,
                         threshold=self.circuit_breaker_threshold)
            return []
        
        try:
            # Add timeout to API call
            jobs = await asyncio.wait_for(
                job_api_manager.search_jobs(constraints),
                timeout=self.timeout
            )
            
            # Reset failure count on success
            self.failure_count = 0
            
            # Tag them
            for job in jobs:
                job["source_layer"] = "MockJobBoard"
            return jobs
            
        except asyncio.TimeoutError:
            self.failure_count += 1
            logger.warning("MockJobBoard API timeout - external_dependency_degraded",
                         timeout=self.timeout,
                         failure_count=self.failure_count,
                         query=query)
            return []
            
        except Exception as e:
            self.failure_count += 1
            # Reclassify as WARNING for external dependency issues
            error_msg = str(e).lower()
            if "getaddrinfo" in error_msg or "connection" in error_msg or "timeout" in error_msg:
                logger.warning("MockJobBoard external_dependency_degraded",
                             error=str(e),
                             failure_count=self.failure_count,
                             query=query)
            else:
                logger.error(f"MockJobBoard failed: {e}",
                           failure_count=self.failure_count)
            return []

class MockStartupDB(DataSource):
    """Simulates a startup database (Crunchbase-like)."""
    
    async def fetch(self, query: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info(f"Fetching from MockStartupDB: {query}")
        await asyncio.sleep(0.5) # Simulate latency
        
        # Hardcoded realistic startups for demo purposes
        startups = [
            {
                "company": "Nebula AI",
                "role": "Senior AI Engineer",
                "location": "San Francisco",
                "skills": ["Python", "PyTorch", "LLM"],
                "funding": "Series A",
                "growth_stage": "High Growth",
                "hiring_urgency": "High",
                "salary_range": "$180k - $250k",
                "source": "startup_db",
                "url": "https://nebula.ai/careers"
            },
            {
                "company": "Quantum Leap",
                "role": "Backend Lead",
                "location": "Remote",
                "skills": ["Go", "Kubernetes", "Distributed Systems"],
                "funding": "Seed",
                "growth_stage": "Early",
                "hiring_urgency": "Medium",
                "salary_range": "$160k - $200k",
                "source": "startup_db",
                "url": "https://quantumleap.io/jobs"
            },
             {
                "company": "EcoTech Solutions",
                "role": "Full Stack Engineer",
                "location": "Berlin",
                "skills": ["React", "Node.js", "TypeScript"],
                "funding": "Series B",
                "growth_stage": "Stable",
                "hiring_urgency": "Low",
                "salary_range": "€80k - €100k",
                "source": "startup_db",
                "url": "https://ecotech.com/jobs"
            }
        ]
        
        # Simple filter based on query/role
        filtered = [s for s in startups if query.lower() in s['role'].lower() or query.lower() in s['skills']]
        if not filtered:
             # Return all if no direct match to ensure we show something in demo
             return startups
        return filtered

class MockCompanyAPI(DataSource):
    """Simulates direct company API integration."""
    
    async def fetch(self, query: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info(f"Fetching from MockCompanyAPI: {query}")
        await asyncio.sleep(0.3)
        
        # Hardcoded data
        companies = [
             {
                "company": "TechGiant Corp",
                "role": "Staff Software Engineer",
                "location": "New York",
                "skills": ["Java", "System Design", "Cloud"],
                "hiring_status": "Active",
                "salary_range": "$220k - $300k",
                "source": "company_api",
                "url": "https://techgiant.com/careers/123"
            }
        ]
        
        filtered = [c for c in companies if query.lower() in c['role'].lower()]
        return filtered if filtered else companies

