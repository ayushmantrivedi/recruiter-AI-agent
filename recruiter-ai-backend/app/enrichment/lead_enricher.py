"""
Lead Enrichment Layer
Injects intelligence and scoring metadata into normalized leads
"""

from typing import Dict, Any, List
from ..utils.logger import get_logger

logger = get_logger("lead_enricher")

class LeadEnricher:
    """
    Enriches normalized leads with intelligence and scoring data.
    Ensures all required DB fields are present before validation.
    """
    
    @classmethod
    def _generate_reasons(cls, signals: Dict[str, Any]) -> List[str]:
        """
        Generate explainability reasons from intelligence signals.
        
        Args:
            signals: Intelligence signals dict
        
        Returns:
            List of human-readable reason strings
        """
        reasons = []
        
        # Hiring pressure
        hiring_pressure = signals.get("hiring_pressure", 0.5)
        if hiring_pressure > 0.7:
            reasons.append("High hiring pressure detected")
        elif hiring_pressure > 0.5:
            reasons.append("Moderate hiring activity")
        
        # Role scarcity
        role_scarcity = signals.get("role_scarcity", 0.5)
        if role_scarcity > 0.7:
            reasons.append("High-demand role with talent scarcity")
        elif role_scarcity > 0.5:
            reasons.append("Competitive talent market")
        
        # Market difficulty
        market_difficulty = signals.get("market_difficulty", 0.5)
        if market_difficulty > 0.7:
            reasons.append("Challenging market conditions")
        elif market_difficulty < 0.3:
            reasons.append("Favorable market conditions")
        
        # Outsourcing likelihood
        outsourcing_likelihood = signals.get("outsourcing_likelihood", 0.5)
        if outsourcing_likelihood < 0.3:
            reasons.append("Low outsourcing risk")
        elif outsourcing_likelihood > 0.7:
            reasons.append("High outsourcing potential")
        
        # Default reason if no signals triggered
        if not reasons:
            reasons.append("Standard market conditions")
        
        return reasons
    
    @classmethod
    def enrich(cls, lead_dict: Dict[str, Any], intelligence: Dict[str, Any], signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a single lead with intelligence and signal data.
        
        Args:
            lead_dict: Normalized lead as dict
            intelligence: Intelligence metadata (role, seniority, location, etc.)
            signals: Intelligence signals (hiring_pressure, role_scarcity, etc.)
        
        Returns:
            Enriched lead dict with all required fields
        """
        enriched = lead_dict.copy()
        
        # 1. Map confidence_score to score and confidence
        if "confidence_score" in enriched:
            # Use confidence_score as the base score
            score_value = enriched.get("confidence_score", 50.0)
            
            # FIXED: Realistic confidence calculation (0.4-0.95 range)
            # Base confidence on score normalization with floor and ceiling
            # Lower scores get lower confidence, but never below 0.4
            # Higher scores get higher confidence, but capped at 0.95
            
            # Normalize score to 0-1 range
            normalized_score = score_value / 100.0
            
            # Apply floor (0.4) and ceiling (0.95) with scaling
            # Formula: 0.4 + (normalized_score * 0.55)
            # This maps: 0 -> 0.4, 50 -> 0.675, 100 -> 0.95
            base_confidence = 0.4 + (normalized_score * 0.55)
            
            # Adjust based on evidence count (if available)
            evidence_count = enriched.get("evidence_count", 0)
            if evidence_count > 0:
                # More evidence = higher confidence (up to +0.05)
                evidence_boost = min(evidence_count * 0.01, 0.05)
                base_confidence = min(base_confidence + evidence_boost, 0.95)
            
            # Adjust based on source reliability
            source = enriched.get("source", "unknown")
            source_reliability = {
                "company_api": 0.05,      # Direct company API = most reliable
                "startup_db": 0.03,       # Curated database = reliable
                "job_board": 0.0,         # Job boards = baseline
                "unknown": -0.05          # Unknown source = less reliable
            }
            reliability_adjustment = source_reliability.get(source, 0.0)
            base_confidence = max(0.4, min(base_confidence + reliability_adjustment, 0.95))
            
            confidence_value = round(base_confidence, 3)
            
            # Only set if not already present
            if "score" not in enriched:
                enriched["score"] = score_value
            if "confidence" not in enriched:
                enriched["confidence"] = confidence_value
        else:
            # No score available, use defaults
            if "score" not in enriched:
                enriched["score"] = 50.0
            if "confidence" not in enriched:
                enriched["confidence"] = 0.5
        
        # 2. Inject intelligence metadata (only if missing)
        if "role" not in enriched and intelligence.get("role"):
            enriched["role"] = intelligence["role"]
        
        if "seniority" not in enriched and intelligence.get("seniority"):
            enriched["seniority"] = intelligence["seniority"]
        
        if "location" not in enriched and intelligence.get("location"):
            enriched["location"] = intelligence["location"]
        
        # 3. Generate reasons from signals (for explainability)
        if "reasons" not in enriched or not enriched["reasons"]:
            enriched["reasons"] = cls._generate_reasons(signals)
        
        # 4. Inject intelligence signals (for future use, not in DB schema currently)
        # These will be stripped by LeadContract but useful for logging/debugging
        if signals:
            enriched["hiring_pressure"] = signals.get("hiring_pressure", 0.5)
            enriched["role_scarcity"] = signals.get("role_scarcity", 0.5)
            enriched["outsourcing_likelihood"] = signals.get("outsourcing_likelihood", 0.5)
            enriched["market_difficulty"] = signals.get("market_difficulty", 0.5)
        
        # 5. Ensure company field is present (required by contract)
        if "company" not in enriched and "company_name" in enriched:
            enriched["company"] = enriched["company_name"]
        elif "company_name" not in enriched and "company" in enriched:
            enriched["company_name"] = enriched["company"]
        
        return enriched
    
    @classmethod
    def enrich_batch(cls, leads: List[Dict[str, Any]], intelligence: Dict[str, Any], signals: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Enrich a batch of leads.
        
        Args:
            leads: List of normalized lead dicts
            intelligence: Intelligence metadata
            signals: Intelligence signals
        
        Returns:
            List of enriched lead dicts
        """
        enriched_leads = []
        
        for lead in leads:
            try:
                enriched = cls.enrich(lead, intelligence, signals)
                enriched_leads.append(enriched)
            except Exception as e:
                logger.error("Failed to enrich lead", 
                           company=lead.get("company_name", "unknown"),
                           error=str(e))
                # Still include the original lead
                enriched_leads.append(lead)
        
        logger.info(f"Enriched {len(enriched_leads)} leads with intelligence data")
        return enriched_leads
