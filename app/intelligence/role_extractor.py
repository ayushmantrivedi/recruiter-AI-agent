from dataclasses import dataclass
from typing import List, Optional
import re
from .market_context import ROLE_SCARCITY, SENIORITY_DIFFICULTY

@dataclass
class RoleProfile:
    role: str
    skills: List[str]
    experience: int
    seniority: str
    location: str

class RoleExtractor:
    
    SKILL_KEYWORDS = ["python", "ml", "ai", "sql", "aws", "react", "node", "java", "golang", "c++", "kubernetes", "docker", "gcp", "azure"]
    
    @staticmethod
    def extract(text: str) -> RoleProfile:
        normalized_text = text.lower()
        
        # 1. Extract Role
        role = "Software Engineer" # Default
        best_match_len = 0
        for known_role in ROLE_SCARCITY.keys():
            if known_role.lower() in normalized_text:
                if len(known_role) > best_match_len:
                    role = known_role
                    best_match_len = len(known_role)
                    
        # Map some common aliases and short forms
        # Check specific keywords if no specific role found yet or to override generic matches
        
        # AI/ML Specific
        if "ml " in normalized_text or "machine learning" in normalized_text:
             role = "ML Engineer"
        elif "ai " in normalized_text or "artificial intelligence" in normalized_text:
             role = "AI Engineer"
        elif "data scientist" in normalized_text or "ds " in normalized_text:
             role = "Data Scientist"
             
        # Engineering Specific
        elif "backend" in normalized_text:
             role = "Backend Engineer"
        elif "frontend" in normalized_text:
             role = "Frontend Engineer"
        elif "devops" in normalized_text:
             role = "DevOps Engineer"
        elif "full stack" in normalized_text or "fullstack" in normalized_text:
             role = "Full Stack Engineer"
        elif "android" in normalized_text:
             role = "Android Developer"
        elif "ios" in normalized_text:
             role = "iOS Developer"
        
        # 2. Extract Skills
        skills = []
        for skill in RoleExtractor.SKILL_KEYWORDS:
            if skill in normalized_text:
                skills.append(skill)
                
        # 3. Extract Experience
        # Regex for patterns like "4+ years", "4 years", "4 yrs", "exp 4"
        experience = 0 # Default
        exp_match = re.search(r'(\d+)\s*\+?\s*(?:year|yrs|yoe|exp)', normalized_text)
        if exp_match:
            try:
                experience = int(exp_match.group(1))
            except ValueError:
                pass
        
        # 4. Extract Seniority
        seniority = "Mid" # Default
        if "senior" in normalized_text or "sr" in normalized_text:
            seniority = "Senior"
        elif "lead" in normalized_text:
            seniority = "Lead"
        elif "junior" in normalized_text or "jr" in normalized_text or "fresher" in normalized_text:
            seniority = "Junior"
        elif "principal" in normalized_text:
            seniority = "Principal"
            
        # Infer seniority from experience if not explicit
        if experience >= 5 and seniority == "Mid":
            seniority = "Senior"
        if experience >= 8 and seniority == "Senior":
            seniority = "Lead"
        if experience <= 2 and seniority == "Mid":
            seniority = "Junior"

        # 5. Extract Location
        location = "Remote" # Default fallback
        # Simple lookup from normalized location list (could be imported)
        # Using the keys from LOCATION_COMPETITION in market_context would be better, 
        # but for now let's check common ones.
        common_locations = ["bangalore", "mumbai", "pune", "delhi", "remote", "hyderabad", "chennai", "ncr", "gurgaon", "noida"]
        
        for loc in common_locations:
            if loc in normalized_text:
                location = loc.title()
                break
                
        # Special case for "blr" -> Bangalore
        if "blr" in normalized_text:
            location = "Bangalore"

        return RoleProfile(
            role=role,
            skills=skills,
            experience=experience,
            seniority=seniority,
            location=location
        )
