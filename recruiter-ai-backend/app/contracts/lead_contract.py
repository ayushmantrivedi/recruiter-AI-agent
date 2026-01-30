"""
Lead Contract - Enforces strict DB schema compliance
Prevents silent data loss from schema mismatches
"""

from typing import Dict, Any, Optional, Set
from ..utils.logger import get_logger

logger = get_logger("lead_contract")

class LeadContract:
    """
    Enforces the contract between ranking/search layer and database persistence.
    Only allows fields that exist in the Lead DB model.
    """
    
    # Fields that exist in the Lead DB model (from database.py)
    ALLOWED_DB_FIELDS: Set[str] = {
        # Primary
        "query_id",
        
        # Company information
        "company_name",
        "company_domain",
        "company_size",
        "industry",
        "role",      # Added for identity/deduplication
        "location",  # Added for identity/deduplication
        
        # Lead scoring
        "score",
        "confidence",
        "reasons",  # JSON
        
        # Contact information
        "linkedin_url",
        "website_url",
        "hiring_manager",
        
        # Evidence data
        "evidence_objects",  # JSON
        "job_postings",  # JSON
        "news_mentions",  # JSON
        
        # Status
        "status",
        "outreach_generated"
    }
    
    # Required fields that must be present
    REQUIRED_FIELDS: Set[str] = {
        "company_name",
        "score",
        "confidence"
    }
    
    # Field aliases for normalization
    FIELD_ALIASES: Dict[str, str] = {
        "company": "company_name",
        "title": "role",  # Not in DB, will be stripped
        "location": "location",  # Not in DB, will be stripped
        "url": "website_url",
        "job_url": "website_url"
    }
    
    @classmethod
    def sanitize(cls, lead_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Sanitize lead data to match DB schema.
        Returns clean dict with only allowed fields, or None if invalid.
        """
        if not isinstance(lead_data, dict):
            logger.warning("Invalid lead data type", type=type(lead_data).__name__)
            return None
        
        clean_lead = {}
        stripped_fields = []
        
        # Process each field
        for key, value in lead_data.items():
            # Normalize aliases
            normalized_key = cls.FIELD_ALIASES.get(key, key)
            
            # Check if field is allowed in DB
            if normalized_key in cls.ALLOWED_DB_FIELDS:
                clean_lead[normalized_key] = value
            else:
                # Strip unknown field
                stripped_fields.append(key)
        
        # Log stripped fields for debugging
        if stripped_fields:
            logger.debug("Stripped non-DB fields from lead",
                        company=clean_lead.get("company_name", "unknown"),
                        stripped=stripped_fields)
        
        # Ensure required fields exist
        if "company_name" not in clean_lead or not clean_lead["company_name"]:
            # Try to recover from 'company' field
            if "company" in lead_data:
                clean_lead["company_name"] = lead_data["company"]
            else:
                clean_lead["company_name"] = "Unknown Company"
                logger.warning("Lead missing company_name, defaulted to 'Unknown Company'")
        
        # Ensure score and confidence
        try:
            clean_lead["score"] = float(clean_lead.get("score", 0.0))
            clean_lead["confidence"] = float(clean_lead.get("confidence", 0.0))
            
            # Clamp values
            clean_lead["score"] = max(0.0, min(100.0, clean_lead["score"]))
            clean_lead["confidence"] = max(0.0, min(1.0, clean_lead["confidence"]))
        except (ValueError, TypeError) as e:
            logger.warning("Invalid score/confidence types", error=str(e))
            clean_lead["score"] = 0.0
            clean_lead["confidence"] = 0.0
        
        # Ensure JSON fields are lists
        for json_field in ["reasons", "evidence_objects", "job_postings", "news_mentions"]:
            if json_field not in clean_lead:
                clean_lead[json_field] = []
            elif not isinstance(clean_lead[json_field], list):
                clean_lead[json_field] = []
        
        return clean_lead
    
    @classmethod
    def validate_required(cls, lead_data: Dict[str, Any]) -> bool:
        """Check if all required fields are present."""
        for field in cls.REQUIRED_FIELDS:
            if field not in lead_data or not lead_data[field]:
                return False
        return True
