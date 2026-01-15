from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List

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
        source = raw_lead.get("source", "unknown")
        
        # Default extractions
        company = raw_lead.get("company") or raw_lead.get("company_name") or "Unknown Company"
        role = raw_lead.get("title") or raw_lead.get("role") or "Unknown Role"
        location = raw_lead.get("location", "Remote")
        url = raw_lead.get("url") or raw_lead.get("job_url") or "#"
        
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
        return [LeadNormalizer.normalize(lead) for lead in raw_leads]
