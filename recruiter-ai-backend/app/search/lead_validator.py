from typing import Dict, Any, Optional
from dataclasses import asdict
from ..utils.logger import get_logger

logger = get_logger("lead_validator")

class LeadValidator:
    """
    Enforces strict schema validation for leads before persistence.
    Acts as a gatekeeper to prevent database constraint violations.
    """
    
    REQUIRED_FIELDS = ["company", "score", "confidence"]
    
    @staticmethod
    def validate_and_fix(lead_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validates lead data and attempts to fix common issues.
        Returns the fixed lead dict or None if irretrievably invalid.
        """
        if not isinstance(lead_data, dict):
            logger.warning("Invalid lead data type", type=type(lead_data))
            return None
            
        # 1. Critical Field: Company
        company = lead_data.get("company")
        if not company:
            # Attempt to recover from company_name alias if present
            company = lead_data.get("company_name")
            
        if not company:
            # Attempt to infer from domain if available
            # logic: user might have domain but no name
            # For now, strictly enforce or default if missing
            company = "Unknown Company"
            logger.warning("Lead missing company name, defaulted to 'Unknown Company'", 
                          url=lead_data.get("job_url", "no-url"))
        
        # Update normalized company
        lead_data["company"] = company
        lead_data["company_name"] = company # Ensure alias is also present for DB model mapping

        # 2. Critical Field: Score & Confidence
        try:
            score = float(lead_data.get("score", 0.0))
            confidence = float(lead_data.get("confidence", 0.0))
            
            # Clamp values
            lead_data["score"] = max(0.0, min(100.0, score))
            lead_data["confidence"] = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            logger.warning("Invalid score/confidence types", 
                          score=lead_data.get("score"), 
                          confidence=lead_data.get("confidence"))
            lead_data["score"] = 0.0
            lead_data["confidence"] = 0.0

        # 3. Ensure other fields expected by DB model exist (even if None/Empty)
        # DB Model: Lead (company_name, company_domain, company_size, industry, reasons, evidence_count, ...)
        
        defaults = {
            "reasons": [],
            "evidence_count": 0,
            "job_postings": [],
            "news_mentions": [],
            "evidence_objects": []
        }
        
        for key, default_val in defaults.items():
            if key not in lead_data or lead_data[key] is None:
                lead_data[key] = default_val

        return lead_data
