import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re
from ..config import settings
from ..utils.logger import get_logger, log_lead_generation
from ..utils.cache import cache

logger = get_logger("signal_judge")


class SignalJudge:
    """Signal Judge agent that scores and ranks hiring leads.

    Purpose: Score companies, rank leads, explain "why now"
    Only reasons from evidence objects, prevents hallucination.
    """

    def __init__(self):
        self.scoring_weights = {
            "job_postings_recent": 0.4,
            "job_postings_volume": 0.2,
            "news_signals": 0.2,
            "company_growth": 0.15,
            "market_timing": 0.05
        }

    async def judge_leads(self, query_id: str, evidence_objects: List[Dict[str, Any]],
                         constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Judge and rank hiring leads from evidence objects.

        Args:
            query_id: Unique query identifier
            evidence_objects: Raw evidence from Action Orchestrator
            constraints: Original search constraints

        Returns:
            Ranked list of lead objects with scores and explanations
        """
        try:
            logger.info("Starting signal judgment", query_id=query_id, evidence_count=len(evidence_objects))

            # Group evidence by company
            company_evidence = self._group_evidence_by_company(evidence_objects)

            leads = []

            for company_name, evidence_list in company_evidence.items():
                # Score the company
                score_result = await self._score_company(company_name, evidence_list, constraints)

                if score_result["score"] > 0:  # Only include companies with some signal
                    lead = {
                        "company": company_name,
                        "score": score_result["score"],
                        "confidence": score_result["confidence"],
                        "reasons": score_result["reasons"],
                        "evidence_count": len(evidence_list),
                        "last_updated": datetime.utcnow().isoformat(),
                        "query_id": query_id
                    }
                    leads.append(lead)

            # Sort by score descending
            ranked_leads = sorted(leads, key=lambda x: x["score"], reverse=True)

            # Log lead generation
            for lead in ranked_leads[:5]:  # Log top 5
                log_lead_generation(
                    query_id=query_id,
                    company=lead["company"],
                    score=lead["score"],
                    reasons=lead["reasons"],
                    evidence_count=lead["evidence_count"]
                )

            logger.info("Signal judgment completed",
                       query_id=query_id,
                       companies_scored=len(company_evidence),
                       leads_generated=len(ranked_leads))

            return ranked_leads

        except Exception as e:
            logger.error("Signal judgment failed", error=str(e), query_id=query_id)
            return []

    def _group_evidence_by_company(self, evidence_objects: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group evidence objects by company name."""
        try:
            company_groups = {}

            for evidence in evidence_objects:
                # Extract company names from different evidence types
                companies = self._extract_companies_from_evidence(evidence)

                for company in companies:
                    if company not in company_groups:
                        company_groups[company] = []
                    company_groups[company].append(evidence)

            logger.debug("Evidence grouped by company",
                        total_evidence=len(evidence_objects),
                        unique_companies=len(company_groups))

            return company_groups

        except Exception as e:
            logger.error("Evidence grouping failed", error=str(e))
            return {}

    def _extract_companies_from_evidence(self, evidence: Dict[str, Any]) -> List[str]:
        """Extract company names from various evidence types."""
        try:
            companies = []

            # Job posting evidence
            if evidence.get("source") in ["arbeitnow", "github_jobs"]:
                company = evidence.get("company", "").strip()
                if company:
                    companies.append(company)

            # News evidence
            elif evidence.get("source") == "mediastack":
                company = evidence.get("company_mentioned", "").strip()
                if company:
                    companies.append(company)

            # Company metadata evidence
            elif evidence.get("source") == "company_metadata":
                company = evidence.get("company_name", "").strip()
                if company:
                    companies.append(company)

            # Multiple jobs in a search result
            if "jobs" in evidence:
                for job in evidence["jobs"]:
                    company = job.get("company", "").strip()
                    if company:
                        companies.append(company)

            # Multiple news articles
            if "news" in evidence:
                for article in evidence["news"]:
                    company = article.get("company_mentioned", "").strip()
                    if company:
                        companies.append(company)

            # Normalize company names (basic cleanup)
            normalized_companies = []
            for company in companies:
                # Remove common suffixes and clean up
                cleaned = self._normalize_company_name(company)
                if cleaned and len(cleaned) > 1:  # Avoid single characters
                    normalized_companies.append(cleaned)

            return list(set(normalized_companies))  # Remove duplicates

        except Exception as e:
            logger.error("Company extraction failed", error=str(e))
            return []

    def _normalize_company_name(self, company_name: str) -> str:
        """Normalize company names for consistent grouping."""
        try:
            # Basic normalization
            normalized = company_name.strip()

            # Remove common suffixes
            suffixes_to_remove = [
                " inc", " Inc", " INC",
                " llc", " LLC",
                " ltd", " Ltd", " LTD",
                " corp", " Corp", " CORP",
                " co", " Co", " CO",
                " gmbh", " GmbH",
                " pty", " Pty"
            ]

            for suffix in suffixes_to_remove:
                if normalized.lower().endswith(suffix.lower()):
                    normalized = normalized[:-len(suffix)].strip()
                    break

            return normalized

        except Exception as e:
            return company_name

    async def _score_company(self, company_name: str, evidence_list: List[Dict[str, Any]],
                           constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Score a company based on its evidence and constraints."""
        try:
            score_components = {
                "job_postings_recent": 0.0,
                "job_postings_volume": 0.0,
                "news_signals": 0.0,
                "company_growth": 0.0,
                "market_timing": 0.0
            }

            reasons = []

            # Analyze job posting evidence
            job_evidence = [e for e in evidence_list if e.get("source") in ["arbeitnow", "github_jobs"]]
            if job_evidence:
                job_score, job_reasons = self._score_job_postings(company_name, job_evidence, constraints)
                score_components["job_postings_recent"] = job_score * 0.7
                score_components["job_postings_volume"] = job_score * 0.3
                reasons.extend(job_reasons)

            # Analyze news evidence
            news_evidence = [e for e in evidence_list if e.get("source") == "mediastack"]
            if news_evidence:
                news_score, news_reasons = self._score_news_signals(company_name, news_evidence)
                score_components["news_signals"] = news_score
                reasons.extend(news_reasons)

            # Analyze company metadata
            metadata_evidence = [e for e in evidence_list if e.get("source") == "company_metadata"]
            if metadata_evidence:
                growth_score, growth_reasons = self._score_company_growth(company_name, metadata_evidence)
                score_components["company_growth"] = growth_score
                reasons.extend(growth_reasons)

            # Calculate market timing (recency factor)
            timing_score, timing_reasons = self._score_market_timing(evidence_list)
            score_components["market_timing"] = timing_score
            reasons.extend(timing_reasons)

            # Calculate final score
            final_score = sum(
                score_components[component] * weight
                for component, weight in self.scoring_weights.items()
            )

            # Calculate confidence based on evidence diversity and volume
            confidence = self._calculate_confidence(evidence_list, score_components)

            result = {
                "score": round(final_score, 2),
                "confidence": round(confidence, 2),
                "reasons": reasons[:10],  # Limit to top 10 reasons
                "score_components": score_components,
                "evidence_types": list(set(e.get("source", "unknown") for e in evidence_list))
            }

            logger.debug("Company scored",
                        company=company_name,
                        score=final_score,
                        confidence=confidence,
                        reasons_count=len(reasons))

            return result

        except Exception as e:
            logger.error("Company scoring failed", error=str(e), company=company_name)
            return {
                "score": 0.0,
                "confidence": 0.0,
                "reasons": ["Scoring failed due to error"],
                "score_components": {},
                "evidence_types": []
            }

    def _score_job_postings(self, company_name: str, job_evidence: List[Dict[str, Any]],
                           constraints: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Score based on job posting patterns."""
        try:
            reasons = []
            score = 0.0

            total_jobs = 0
            recent_jobs = 0
            relevant_jobs = 0

            # Analyze all job evidence
            for evidence in job_evidence:
                jobs = evidence.get("jobs", [])
                total_jobs += len(jobs)

                for job in jobs:
                    if job.get("company", "").lower() == company_name.lower():
                        relevant_jobs += 1

                        # Check if job matches role constraints
                        job_title = job.get("title", "").lower()
                        role = constraints.get("role", "").lower() if constraints.get("role") else ""

                        if role and role in job_title:
                            score += 0.3
                            reasons.append(f"Posted {job.get('title', 'job')} matching role requirements")

                        # Check recency (simplified - in production would parse dates)
                        posted_date = job.get("posted_date", "")
                        if posted_date:  # Assume recent if we have a date
                            recent_jobs += 1
                            score += 0.2

            # Volume scoring
            if relevant_jobs >= constraints.get("min_job_posts", 1):
                volume_bonus = min(1.0, relevant_jobs / 10.0)  # Cap at 10 jobs
                score += volume_bonus
                reasons.append(f"{relevant_jobs} relevant job postings found")

            # Recency bonus
            if recent_jobs > 0:
                recency_bonus = min(0.5, recent_jobs / 5.0)
                score += recency_bonus
                reasons.append(f"{recent_jobs} recent job postings")

            return min(1.0, score), reasons

        except Exception as e:
            logger.error("Job posting scoring failed", error=str(e))
            return 0.0, ["Job posting analysis failed"]

    def _score_news_signals(self, company_name: str, news_evidence: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Score based on news and PR signals."""
        try:
            reasons = []
            score = 0.0

            growth_keywords = ["hiring", "expansion", "funding", "growth", "new office", "series", "raised"]
            hiring_keywords = ["hiring", "recruiting", "talent", "engineer", "developer"]

            for evidence in news_evidence:
                articles = evidence.get("news", [])

                for article in articles:
                    title = article.get("title", "").lower()
                    description = article.get("description", "").lower()

                    # Growth signals
                    for keyword in growth_keywords:
                        if keyword in title or keyword in description:
                            score += 0.4
                            reasons.append(f"Growth signal: {keyword} mentioned in '{article.get('title', '')}'")
                            break

                    # Hiring signals
                    for keyword in hiring_keywords:
                        if keyword in title or keyword in description:
                            score += 0.3
                            reasons.append(f"Hiring signal: {keyword} mentioned in news")
                            break

            return min(1.0, score), reasons

        except Exception as e:
            logger.error("News signal scoring failed", error=str(e))
            return 0.0, ["News analysis failed"]

    def _score_company_growth(self, company_name: str, metadata_evidence: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Score based on company growth indicators."""
        try:
            reasons = []
            score = 0.0

            for evidence in metadata_evidence:
                growth_indicators = evidence.get("growth_indicators", [])

                for indicator in growth_indicators:
                    indicator_type = indicator.get("type", "")
                    if "funding" in indicator_type or "investment" in indicator_type:
                        score += 0.5
                        reasons.append("Recent funding round detected")
                    elif "hiring" in indicator_type:
                        score += 0.3
                        reasons.append("Active hiring expansion")
                    elif "expansion" in indicator_type:
                        score += 0.4
                        reasons.append("Company expansion plans")

            return min(1.0, score), reasons

        except Exception as e:
            logger.error("Company growth scoring failed", error=str(e))
            return 0.0, ["Growth analysis failed"]

    def _score_market_timing(self, evidence_list: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Score based on market timing and urgency signals."""
        try:
            reasons = []
            score = 0.0

            # Look for urgency indicators
            urgency_patterns = [
                r"immediate.*hire",
                r"urgent.*requirement",
                r"asap",
                r"critical.*position",
                r"must.*fill"
            ]

            for evidence in evidence_list:
                if evidence.get("source") in ["arbeitnow", "github_jobs"]:
                    jobs = evidence.get("jobs", [])
                    for job in jobs:
                        description = job.get("description", "").lower()
                        title = job.get("title", "").lower()

                        for pattern in urgency_patterns:
                            if re.search(pattern, title + " " + description):
                                score += 0.3
                                reasons.append("Urgent hiring language detected")
                                break

            # Recency bonus for very recent evidence
            # In production, would check actual dates
            score += 0.1  # Base recency score

            return min(1.0, score), reasons

        except Exception as e:
            logger.error("Market timing scoring failed", error=str(e))
            return 0.0, ["Timing analysis failed"]

    def _calculate_confidence(self, evidence_list: List[Dict[str, Any]],
                            score_components: Dict[str, float]) -> float:
        """Calculate confidence in the scoring based on evidence quality and diversity."""
        try:
            # Base confidence on evidence volume
            evidence_count = len(evidence_list)
            volume_confidence = min(0.6, evidence_count / 10.0)  # Max at 10 pieces of evidence

            # Diversity bonus (different evidence types)
            evidence_types = set(e.get("source", "unknown") for e in evidence_list)
            diversity_confidence = min(0.3, len(evidence_types) / 3.0)  # Max at 3 different types

            # Score consistency bonus
            avg_score = sum(score_components.values()) / len(score_components) if score_components else 0.0
            consistency_confidence = min(0.1, avg_score)  # Higher scores = higher confidence

            total_confidence = volume_confidence + diversity_confidence + consistency_confidence
            return min(1.0, total_confidence)

        except Exception as e:
            logger.error("Confidence calculation failed", error=str(e))
            return 0.5


# Global signal judge instance
signal_judge = SignalJudge()
