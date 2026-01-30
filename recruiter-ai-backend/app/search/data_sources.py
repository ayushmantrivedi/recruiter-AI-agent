
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any

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
            from ..apis.job_apis import job_api_manager
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


class RealTimeWebScraper(DataSource):
    """Scrapes real-time job data from search engines (DuckDuckGo)."""
    
    async def fetch(self, query: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        from bs4 import BeautifulSoup
        import urllib.parse
        
        logger.info(f"RealTimeWebScraper: Searching for '{query}'")
        
        role = constraints.get("role", query)
        location = constraints.get("location", "Remote")
        
        # Construct a targeted search query
        # We target specific reliable job sites via search operators
        search_query = f'{role} jobs {location} site:linkedin.com/jobs OR site:indeed.com OR site:greenhouse.io'
        encoded_query = urllib.parse.quote(search_query)
        
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://duckduckgo.com/"
        }
        
        try:
            # Use httpx to fetch HTML directly with STRICT timeout
            # We fail fast (4s) so we don't block the main API results
            async with httpx.AsyncClient(timeout=4.0) as client:
                # DuckDuckGo HTML endpoint requires POST with 'q'
                resp = await client.post(url, data={"q": search_query}, headers=headers)
                
                if resp.status_code != 200:
                    logger.warning("DuckDuckGo scrape failed", status=resp.status_code)
                    return []
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                results = []
                # Parse DDG HTML results
                # Structure: <div class="result"> <h2 class="result__title"> <a href="...">...</a> </h2> <div class="result__snippet">...</div> </div>
                
                for i, row in enumerate(soup.find_all('div', class_='result', limit=10)):
                    try:
                        title_tag = row.find('h2', class_='result__title')
                        if not title_tag: continue
                        
                        link_tag = title_tag.find('a')
                        if not link_tag: continue
                        
                        title_text = link_tag.get_text(strip=True)
                        url_href = link_tag.get('href', '')
                        
                        snippet_tag = row.find('a', class_='result__snippet')
                        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                        
                        # Extract company - often in title "Role at Company" or snippet
                        company = "Unknown"
                        if " at " in title_text:
                            parts = title_text.split(" at ")
                            company = parts[-1].split("|")[0].strip() # Simple heuristic
                        elif "|" in title_text:
                             parts = title_text.split("|")
                             company = parts[-1].strip()
                        elif "-" in title_text:
                            parts = title_text.split("-")
                            company = parts[-1].strip()
                            
                        # Cleanup company name (remove common suffixes from page titles)
                        company = company.replace("LinkedIn", "").replace("Indeed", "").replace("Greenhouse", "").strip()
                        if not company: company = "Confidential"
                        
                        results.append({
                            "title": title_text,
                            "company": company,
                            "location": location, # Inferred from query context
                            "description": snippet,
                            "url": url_href,
                            "posted_date": "Recently",
                            "source": "WebScraper (Real-Time)",
                            "job_type": ["full-time"],
                            "tags": ["Active Hiring"]
                        })
                        
                    except Exception as parse_error:
                        continue
                        
                logger.info("RealTimeWebScraper success", leads_found=len(results))
                return results

        except Exception as e:
            logger.error(f"RealTimeWebScraper failed: {str(e)}")
            return []


class MockCompanyAPI(DataSource):
    """Simple static fallback data (disabled by default in production)."""
    
    async def fetch(self, query: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [] # Keep this one empty for now to avoid noise
