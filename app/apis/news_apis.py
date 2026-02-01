import asyncio
import json
from typing import Dict, Any, List, Optional
import httpx
from ..config import settings
from ..utils.logger import get_logger, log_api_call
from ..utils.cache import cache

logger = get_logger("news_apis")


class NewsAPIManager:
    """Manager for news and company information APIs."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def fetch_company_news(self, company_name: str, days_back: int = 30) -> Dict[str, Any]:
        """Fetch recent news about a company using Mediastack API.

        API: https://mediastack.com
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Check if we have API key
            if not settings.api.openai_api_key:  # Using OpenAI key as placeholder for now
                logger.warning("No Mediastack API key configured, skipping news fetch")
                return {"news": [], "total_count": 0, "source": "mediastack", "error": "API key not configured"}

            # Check rate limit
            rate_limit_key = "rate_limit:mediastack"
            can_proceed = await cache.check_rate_limit(
                rate_limit_key,
                settings.api.mediastack_rate_limit,
                86400  # 24 hour window
            )

            if not can_proceed:
                logger.warning("Mediastack rate limit exceeded")
                return {"news": [], "total_count": 0, "source": "mediastack", "error": "Rate limit exceeded"}

            # Build query - search for company name in news
            params = {
                "access_key": "your_mediastack_api_key_here",  # Would be from settings
                "keywords": company_name,
                "languages": "en",
                "limit": 10,
                "sort": "published_desc"
            }

            url = "http://api.mediastack.com/v1/news"
            logger.info("Fetching company news", company=company_name, days_back=days_back)

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            # Process and standardize news articles
            news_articles = []
            for article in data.get("data", []):
                standardized_article = {
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", ""),
                    "published_at": article.get("published_at", ""),
                    "author": article.get("author", ""),
                    "category": article.get("category", ""),
                    "company_mentioned": company_name,
                    "relevance_score": self._calculate_relevance_score(article, company_name)
                }
                news_articles.append(standardized_article)

            # Filter by recency and relevance
            recent_articles = [
                article for article in news_articles
                if article["relevance_score"] > 0.3  # Minimum relevance threshold
            ]

            result = {
                "news": recent_articles,
                "total_count": len(recent_articles),
                "source": "mediastack",
                "company": company_name,
                "days_back": days_back
            }

            # Log API call
            latency = asyncio.get_event_loop().time() - start_time
            log_api_call(
                tool_name="mediastack",
                endpoint=url,
                latency=latency,
                cost=0.0,  # Free tier
                success=True,
                articles_found=len(recent_articles)
            )

            return result

        except Exception as e:
            latency = asyncio.get_event_loop().time() - start_time
            log_api_call(
                tool_name="mediastack",
                endpoint="http://api.mediastack.com/v1/news",
                latency=latency,
                cost=0.0,
                success=False,
                error=str(e)
            )
            logger.error("Mediastack API call failed", error=str(e), company=company_name)
            return {"news": [], "total_count": 0, "source": "mediastack", "error": str(e)}

    def _calculate_relevance_score(self, article: Dict[str, Any], company_name: str) -> float:
        """Calculate how relevant a news article is to the company."""
        try:
            title = article.get("title", "").lower()
            description = article.get("description", "").lower()
            company_lower = company_name.lower()

            # Simple relevance scoring based on keyword matches
            score = 0.0

            # Company name in title (high relevance)
            if company_lower in title:
                score += 0.8

            # Company name in description
            if company_lower in description:
                score += 0.4

            # Hiring/recruitment related keywords
            hiring_keywords = ["hire", "recruit", "job", "talent", "engineer", "developer", "growth", "expansion"]
            if any(keyword in title or keyword in description for keyword in hiring_keywords):
                score += 0.3

            # Company size/valuation mentions
            business_keywords = ["funding", "series", "valuation", "ipo", "acquisition", "layoff"]
            if any(keyword in title or keyword in description for keyword in business_keywords):
                score += 0.2

            return min(1.0, score)  # Cap at 1.0

        except Exception as e:
            logger.error("Relevance scoring failed", error=str(e))
            return 0.0

    async def fetch_company_growth_signals(self, company_name: str) -> Dict[str, Any]:
        """Fetch company growth signals from multiple sources."""
        try:
            # For now, use a simple heuristic-based approach
            # In production, this would integrate with Crunchbase, LinkedIn, etc.

            signals = {
                "company": company_name,
                "growth_indicators": [],
                "funding_rounds": [],
                "key_hiring_signals": [],
                "expansion_plans": [],
                "source": "multiple",
                "last_updated": None
            }

            # Try to get news-based signals
            news_result = await self.fetch_company_news(company_name, days_back=90)

            if news_result.get("news"):
                # Analyze news for growth signals
                growth_keywords = [
                    "funding", "series", "raised", "investment", "growth", "expansion",
                    "hiring", "new office", "opening", "launch", "acquisition"
                ]

                for article in news_result["news"]:
                    title = article.get("title", "").lower()
                    desc = article.get("description", "").lower()

                    for keyword in growth_keywords:
                        if keyword in title or keyword in desc:
                            signals["growth_indicators"].append({
                                "type": "news_mention",
                                "keyword": keyword,
                                "title": article.get("title"),
                                "url": article.get("url"),
                                "published_at": article.get("published_at")
                            })
                            break

            logger.info("Company growth signals fetched",
                       company=company_name,
                       signals_found=len(signals["growth_indicators"]))

            return signals

        except Exception as e:
            logger.error("Company growth signals fetch failed", error=str(e), company=company_name)
            return {
                "company": company_name,
                "growth_indicators": [],
                "error": str(e)
            }


# Global news API manager
news_api_manager = NewsAPIManager()
