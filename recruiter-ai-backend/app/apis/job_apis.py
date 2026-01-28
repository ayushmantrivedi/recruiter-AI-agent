import asyncio
import json
from typing import Dict, Any, List, Optional
import httpx
from ..config import settings
from ..utils.logger import get_logger, log_api_call
from ..utils.cache import cache

logger = get_logger("job_apis")


class JobAPIManager:
    """Manager for free job board APIs."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def fetch_arbeitnow_jobs(self, query: str = "", location: str = "", limit: int = 50) -> Dict[str, Any]:
        """Fetch jobs from Arbeitnow API (free, no key required).

        API: https://www.arbeitnow.com/api/job-board-api
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Build query parameters
            params = {
                "search": query,
                "location": location,
                "limit": min(limit, 100)  # API limit
            }

            url = "https://www.arbeitnow.com/api/job-board-api"
            logger.info("Fetching Arbeitnow jobs", params=params)

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Process and standardize response
            jobs = []
            for job in data.get("data", []):
                standardized_job = {
                    "title": job.get("title", ""),
                    "company": job.get("company_name", ""),
                    "location": job.get("location", ""),
                    "description": job.get("description", ""),
                    "url": job.get("url", ""),
                    "posted_date": job.get("created_at", ""),
                    "source": "arbeitnow",
                    "job_type": job.get("job_types", []),
                    "tags": job.get("tags", [])
                }
                jobs.append(standardized_job)

            result = {
                "jobs": jobs,
                "total_count": len(jobs),
                "source": "arbeitnow",
                "query": query,
                "location": location
            }

            # Log API call
            latency = asyncio.get_event_loop().time() - start_time
            log_api_call(
                api_name="arbeitnow",
                endpoint=url,
                success=True,
                latency=latency,
                jobs_found=len(jobs)
            )

            return result

        except Exception as e:
            latency = asyncio.get_event_loop().time() - start_time
            log_api_call(
                api_name="arbeitnow",
                endpoint="https://www.arbeitnow.com/api/job-board-api",
                success=False,
                latency=latency,
                error=str(e)
            )
            logger.error("Arbeitnow API call failed", error=str(e))
            return {"jobs": [], "total_count": 0, "source": "arbeitnow", "error": str(e)}

    async def fetch_remoteok_jobs(self, query: str = "", limit: int = 50) -> Dict[str, Any]:
        """Fetch jobs from RemoteOK API (free, no key required, global coverage).

        API: https://remoteok.com/api
        """
        start_time = asyncio.get_event_loop().time()

        try:
            url = "https://remoteok.com/api"
            headers = {"User-Agent": "RecruiterAI/1.0"}  # Required by RemoteOK
            
            logger.info("Fetching RemoteOK jobs", query=query)

            response = await self.client.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            
            # RemoteOK returns array, first element is metadata
            jobs_data = data[1:] if len(data) > 1 else []

            # Filter by query if provided (multi-word fuzzy matching)
            if query:
                # Extract meaningful keywords (skip common words)
                stop_words = {'with', 'and', 'or', 'the', 'a', 'an', 'in', 'for', 'of', 'to', 'need', 'want', 'looking', 'experience', 'year', 'years', 'urgently'}
                query_words = [w.lower() for w in query.split() if len(w) > 2 and w.lower() not in stop_words]
                
                def job_matches(job):
                    job_text = (
                        job.get("position", "").lower() + " " +
                        job.get("company", "").lower() + " " +
                        " ".join(job.get("tags", []))
                    ).lower()
                    # Match if ANY keyword is found
                    return any(word in job_text for word in query_words)
                
                jobs_data = [j for j in jobs_data if job_matches(j)]

            # Standardize response
            jobs = []
            for job in jobs_data[:limit]:
                standardized_job = {
                    "title": job.get("position", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", "Remote"),
                    "description": job.get("description", "")[:500],
                    "url": job.get("url", ""),
                    "posted_date": job.get("date", ""),
                    "source": "remoteok",
                    "job_type": ["remote"],
                    "tags": job.get("tags", []),
                    "salary": job.get("salary", "")
                }
                jobs.append(standardized_job)

            result = {
                "jobs": jobs,
                "total_count": len(jobs),
                "source": "remoteok",
                "query": query
            }

            latency = asyncio.get_event_loop().time() - start_time
            log_api_call(
                api_name="remoteok",
                endpoint=url,
                success=True,
                latency=latency,
                jobs_found=len(jobs)
            )

            return result

        except Exception as e:
            latency = asyncio.get_event_loop().time() - start_time
            log_api_call(
                api_name="remoteok",
                endpoint="https://remoteok.com/api",
                success=False,
                latency=latency,
                error=str(e)
            )
            logger.error("RemoteOK API call failed", error=str(e))
            return {"jobs": [], "total_count": 0, "source": "remoteok", "error": str(e)}

    async def fetch_github_jobs(self, description: str = "", location: str = "", limit: int = 50) -> Dict[str, Any]:
        """Fetch jobs from GitHub Jobs API (free).

        API: https://jobs.github.com/positions.json
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Check rate limit
            rate_limit_key = "rate_limit:github_jobs"
            can_proceed = await cache.check_rate_limit(
                rate_limit_key,
                settings.api.github_jobs_rate_limit,
                3600  # 1 hour window
            )

            if not can_proceed:
                logger.warning("GitHub Jobs rate limit exceeded")
                return {"jobs": [], "total_count": 0, "source": "github_jobs", "error": "Rate limit exceeded"}

            params = {
                "description": description,
                "location": location
            }

            url = "https://jobs.github.com/positions.json"
            logger.info("Fetching GitHub jobs", params=params)

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            jobs_data = response.json()

            # Standardize response
            jobs = []
            for job in jobs_data[:limit]:  # Apply our own limit
                standardized_job = {
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", ""),
                    "description": job.get("description", ""),
                    "url": job.get("url", ""),
                    "posted_date": job.get("created_at", ""),
                    "source": "github_jobs",
                    "job_type": job.get("type", ""),
                    "tags": []
                }
                jobs.append(standardized_job)

            result = {
                "jobs": jobs,
                "total_count": len(jobs),
                "source": "github_jobs",
                "query": description,
                "location": location
            }

            # Log API call
            latency = asyncio.get_event_loop().time() - start_time
            log_api_call(
                api_name="github_jobs",
                endpoint=url,
                success=True,
                latency=latency,
                jobs_found=len(jobs)
            )

            return result

        except Exception as e:
            latency = asyncio.get_event_loop().time() - start_time
            log_api_call(
                api_name="github_jobs",
                endpoint="https://jobs.github.com/positions.json",
                success=False,
                latency=latency,
                error=str(e)
            )
            logger.error("GitHub Jobs API call failed", error=str(e))
            return {"jobs": [], "total_count": 0, "source": "github_jobs", "error": str(e)}

    async def search_jobs(self, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search multiple job APIs based on constraints.

        Args:
            constraints: Concept reasoner output with role, region, etc.

        Returns:
            List of standardized job results from all APIs
        """
        try:
            # Extract search parameters from constraints
            role = constraints.get("role", "")
            region = constraints.get("region", "remote")
            min_posts = constraints.get("min_job_posts", 1)

            # Parallel API calls
            tasks = []
            if settings.agent.enable_arbeitnow:
                tasks.append(self.fetch_arbeitnow_jobs(query=role, location=region, limit=min_posts * 2))
            
            # Always call RemoteOK for global remote job coverage
            tasks.append(self.fetch_remoteok_jobs(query=role, limit=min_posts * 3))
                
            if settings.agent.enable_github_jobs:
                tasks.append(self.fetch_github_jobs(description=role, location=region, limit=min_posts * 2))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Combine results
            all_jobs = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error("Job API task failed", error=str(result))
                    continue

                if result and "jobs" in result:
                    all_jobs.extend(result["jobs"])

            # Remove duplicates based on URL
            seen_urls = set()
            unique_jobs = []
            for job in all_jobs:
                url = job.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_jobs.append(job)

            logger.info("Job search completed",
                       apis_called=len(tasks),
                       total_jobs=len(all_jobs),
                       unique_jobs=len(unique_jobs))

            return unique_jobs

        except Exception as e:
            logger.error("Job search failed", error=str(e))
            return []


# Global job API manager
job_api_manager = JobAPIManager()
