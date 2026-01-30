from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
import re

@dataclass
class NormalizedLead:
    company_name: str
    role: str
    location: str
    job_url: str
    source: str
    skills: List[str]
    salary_range: Optional[str] = None
    hiring_urgency: str = "Unknown"
    company_growth_stage: str = "Unknown"
    funding_stage: str = "Unknown"
    confidence_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class LeadNormalizer:
    """Normalizes raw data from various sources into a unified schema."""
    
    @staticmethod
    def normalize(raw_lead: Dict[str, Any]) -> NormalizedLead:
        """
        Normalize raw lead data with required field enforcement.
        Returns None if lead is invalid (missing required fields).
        """
        from ..utils.logger import get_logger
        logger = get_logger("lead_normalizer")
        
        source = raw_lead.get("source", "unknown")
        
        # Default extractions
        # Priority: company -> company_name -> Unknown
        company = raw_lead.get("company") or raw_lead.get("company_name") or "Unknown Company"
        role = raw_lead.get("title") or raw_lead.get("role") or "Unknown Role"
        location = raw_lead.get("location") or "Remote"

        # COMPANY HARDENING: Strip legal suffixes and noise
        company = re.sub(r'\s+(GmbH|AG|Ltd|Corp|Inc|LLC|Pvt|Ltd\.|S\.A\.|KGaA|e.V.)\b', '', company, flags=re.IGNORECASE).strip()
        
        # ROLE HARDENING: Strip common noise that breaks deduplication
        # Remove gender markers like (m/f/d), (w/m/d), (all genders)
        role = re.sub(r'\s*\(?[mwfdx]\s*/\s*[mwfdx]\s*/\s*[mwfdx]\)?', '', role, flags=re.IGNORECASE)
        role = re.sub(r'\s*\(\s*all\s*genders\s*\)', '', role, flags=re.IGNORECASE)
        
        # Aggressive Title Cleaning: "Senior Python Developer" -> "Python Developer"
        # We preserve the original title in the object but use the cleaned one for internal logic if needed
        # Actually, for "Best-in-Class", we should probably keep the original title for display but use a 'clean_title' for dedup.
        # But for now, let's keep it simple and clean the main field as requested.
        role = re.sub(r'\b(Senior|Junior|Lead|Principal|Staff|Senior\s+Level|Junior\s+Level)\b', '', role, flags=re.IGNORECASE).strip()
        
        # LOCATION HARDENING: Normalize common patterns
        if "," in location:
            location = location.split(",")[0].strip()
             
        url = raw_lead.get("url") or raw_lead.get("job_url") or "#"
        
        # Required field validation
        # Skip leads missing critical fields
        if not company or company == "Unknown Company":
            logger.warning("Skipping lead with missing company",
                         raw_data=raw_lead,
                         reason="missing_company")
            return None
        
        if not role or role == "Unknown Role":
            logger.warning("Skipping lead with missing role",
                         company=company,
                         raw_data=raw_lead,
                         reason="missing_role")
            return None
        
        if not source or source == "unknown":
            logger.warning("Skipping lead with missing source",
                         company=company,
                         role=role,
                         reason="missing_source")
            return None
        
        # Skills extraction (could be list or string)
        skills = raw_lead.get("skills", [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",")]
        # Also check tags
        if "tags" in raw_lead and isinstance(raw_lead["tags"], list):
            skills.extend(raw_lead["tags"])
            
        # Specific source handling
        urgency = raw_lead.get("hiring_urgency", "Unknown")
        growth = raw_lead.get("growth_stage", "Unknown")
        funding = raw_lead.get("funding", "Unknown")
        salary = raw_lead.get("salary_range")
        
        # Inferred urgency from description if not present
        if urgency == "Unknown" and "description" in raw_lead:
            desc = raw_lead["description"].lower()
            if "urgent" in desc or "immediate" in desc:
                urgency = "High"
            elif "asap" in desc:
                urgency = "High"
                
        return NormalizedLead(
            company_name=company,
            role=role,
            location=location,
            job_url=url,
            source=source,
            skills=list(set(skills)), # dedup
            salary_range=salary,
            hiring_urgency=urgency,
            company_growth_stage=growth,
            funding_stage=funding
        )

    @staticmethod
    def batch_normalize(raw_leads: List[Dict[str, Any]]) -> List[NormalizedLead]:
        """Normalize batch of leads, skipping invalid ones."""
        from ..utils.logger import get_logger
        logger = get_logger("lead_normalizer")
        
        normalized = []
        skipped_count = 0
        
        for raw_lead in raw_leads:
            try:
                normalized_lead = LeadNormalizer.normalize(raw_lead)
                if normalized_lead is not None:
                    normalized.append(normalized_lead)
                else:
                    skipped_count += 1
            except Exception as e:
                skipped_count += 1
                logger.error("Failed to normalize lead",
                           error=str(e),
                           raw_data=raw_lead)
        
        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} invalid leads during normalization",
                       total_raw=len(raw_leads),
                       normalized=len(normalized))
        
        return normalized
