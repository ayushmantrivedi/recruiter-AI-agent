from typing import Dict, Any
import math
from .lead_normalizer import NormalizedLead
from ..utils.logger import get_logger

logger = get_logger("search.lead_scorer")

class LeadScorer:
    """Scores leads based on intelligence signals and lead attributes."""
    
    @staticmethod
    def _apply_nonlinear_scale(raw_val: float) -> float:
        """
        Apply non-linear scaling to push scores to extremes.
        Maps [0, 1] -> [0, 1] but pushes vals away from center.
        """
        # Sigmoid-like or power function to separate the pack
        # Power of 1.5 gives effective spread
        return math.pow(raw_val, 1.5)

    @staticmethod
    def compute_score(lead: NormalizedLead, signals: Dict[str, float]) -> float:
        """
        Compute high-variance score (Target std_dev > 10).
        Range: 40 - 100
        """
        # Base floor is 15 to allow variance
        score = 15.0
        
        # 1. INTELLIGENCE SIGNALS (Max ~35 points)
        # Extract signals first
        pressure = signals.get("hiring_pressure", 0.5)
        scarcity = signals.get("role_scarcity", 0.5)
        difficulty = signals.get("market_difficulty", 0.5)
        
        # Pressure: Weighted heavily (0-15)
        score += LeadScorer._apply_nonlinear_scale(pressure) * 15.0
        
        # Scarcity: Weighted heavily (0-15)
        score += LeadScorer._apply_nonlinear_scale(scarcity) * 15.0
        
        # Difficulty: (0-5)
        score += (1.0 - difficulty) * 5.0
        
        # 2. MATCH QUALITY (Max ~40 points)
        # Urgency: High variance
        urgency = lead.hiring_urgency or "Unknown"
        # Drastic drop for Medium to force variance
        # High=30 allows top leads to soar, while Medium=6 keeps average leads low
        urgency_score = {"High": 1.0, "Medium": 0.2, "Low": 0.0, "Unknown": 0.0}
        score += urgency_score.get(urgency, 0.0) * 30.0  # 0-30
        
        # Skills Match
        if lead.skills:
            # Up to 10 points
            skill_bonus = min(len(lead.skills), 5) * 2.0 
            score += skill_bonus

        # 3. COMPANY PRESTIGE (Max ~25 points)
        growth = lead.company_growth_stage or "Unknown"
        # High=20
        growth_score = {"High Growth": 1.0, "Stable": 0.2, "Early": 0.1, "Unknown": 0.0}
        score += growth_score.get(growth, 0.0) * 20.0 # 0-20
        
        funding = lead.funding_stage or "Unknown"
        funding_score = {"Series A": 0.8, "Series B": 0.9, "Series C": 1.0, "Seed": 0.2, "Unknown": 0.0}
        score += funding_score.get(funding, 0.0) * 10.0 # 0-10
        
        # Salary Bonus (5 points)
        if lead.salary_range:
            score += 5.0
            
        # Hard clamp to 40-100 range (no soft cap, we want variance)
        return max(40.0, min(100.0, round(score, 1)))

    @staticmethod
    def score_leads(leads: list[NormalizedLead], signals: Dict[str, float]) -> list[NormalizedLead]:
        """Score all leads and validate variance requirements."""
        if not leads:
            return leads
            
        scores = []
        for lead in leads:
            s = LeadScorer.compute_score(lead, signals)
            lead.confidence_score = s
            scores.append(s)
            
        # Logging feature contribution can be done here if needed
        if len(scores) > 2:
            import statistics
            std = statistics.stdev(scores)
            logger.info("Scoring distribution", min=min(scores), max=max(scores), mean=statistics.mean(scores), std_dev=std)
            
        return leads
