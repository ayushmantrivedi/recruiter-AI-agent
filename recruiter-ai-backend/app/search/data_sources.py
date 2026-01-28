
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
    """Wraps the real JobAPIManager (Arbeitnow, GitHub, etc.)."""
    
    def __init__(self):
        from ..config import settings
        self.timeout = settings.agent.external_api_timeout
        self.circuit_breaker_threshold = settings.agent.external_api_circuit_breaker_threshold
        self.failure_count = 0
    
    async def fetch(self, query: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info(f"Fetching from JobAPIManager: {query}")
        
        # Circuit breaker check
        if self.failure_count >= self.circuit_breaker_threshold:
            logger.warning("Circuit breaker OPEN - skipping API call",
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
                job["source_layer"] = "RealJobAPI"
            return jobs
            
        except asyncio.TimeoutError:
            self.failure_count += 1
            logger.warning("JobAPI timeout",
                         timeout=self.timeout,
                         failure_count=self.failure_count,
                         query=query)
            return []
            
        except Exception as e:
            self.failure_count += 1
            logger.warning("JobAPI external_dependency_degraded",
                         error=str(e),
                         failure_count=self.failure_count,
                         query=query)
            return []


class MockStartupDB(DataSource):
    """Simple static fallback data (disabled by default in production)."""
    
    async def fetch(self, query: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info(f"MockStartupDB: {query} (fallback mode)")
        await asyncio.sleep(0.1)
        
        # Return empty - real APIs should be used
        # This is only a fallback when all else fails
        return []


class MockCompanyAPI(DataSource):
    """Simple static fallback data (disabled by default in production)."""
    
    async def fetch(self, query: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info(f"MockCompanyAPI: {query} (fallback mode)")
        await asyncio.sleep(0.1)
        
        # Return empty - real APIs should be used
        return []
