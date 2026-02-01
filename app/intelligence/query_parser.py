from typing import List, Optional
import re
from dataclasses import dataclass

@dataclass
class ParsedQuery:
    raw: str
    normalized: str
    tokens: List[str]

class QueryParser:
    @staticmethod
    def parse(query: str) -> ParsedQuery:
        """
        Normalize text, tokenize, and return ParsedQuery object.
        """
        raw = query
        normalized = query.lower().strip()
        
        # Remove special characters but keep alphanumeric and spaces
        # keeping + for experience (e.g., 4+)
        normalized = re.sub(r'[^a-z0-9\s\+]', '', normalized)
        
        tokens = normalized.split()
        
        return ParsedQuery(
            raw=raw,
            normalized=normalized,
            tokens=tokens
        )

class AsyncQueryParser:
    """Async wrapper that extracts structured information from queries."""
    
    ROLE_KEYWORDS = {
        'developer', 'engineer', 'architect', 'manager', 'designer',
        'analyst', 'scientist', 'lead', 'director', 'specialist',
        'consultant', 'administrator', 'devops', 'sre', 'qa', 'tester'
    }
    
    SKILL_KEYWORDS = {
        'python', 'java', 'javascript', 'typescript', 'react', 'node',
        'aws', 'azure', 'gcp', 'kubernetes', 'docker', 'sql', 'nosql',
        'mongodb', 'postgresql', 'redis', 'kafka', 'spark', 'ml',
        'machine learning', 'ai', 'deep learning', 'tensorflow', 'pytorch',
        'golang', 'rust', 'c++', 'scala', 'ruby', 'php', 'swift', 'kotlin'
    }
    
    LOCATION_KEYWORDS = {
        'remote', 'onsite', 'hybrid', 'sf', 'nyc', 'seattle', 'austin',
        'boston', 'london', 'berlin', 'bangalore', 'singapore', 'tokyo',
        'san francisco', 'new york', 'sf', 'nyc'
    }
    
    async def parse(self, query: str) -> dict:
        """Parse query and extract structured information."""
        # Get basic parsing
        parsed = QueryParser.parse(query)
        tokens = parsed.tokens
        normalized = parsed.normalized
        
        # Extract role
        role = self._extract_role(tokens, normalized)
        
        # Extract skills
        skills = self._extract_skills(tokens, normalized)
        
        # Extract location
        location = self._extract_location(tokens, normalized)
        
        # Extract experience
        experience = self._extract_experience(normalized)
        
        # Extract keywords (top 5 meaningful tokens)
        keywords = [t for t in tokens if len(t) > 2 and t not in {'the', 'and', 'for', 'with'}][:5]
        
        return {
            "role": role,
            "location": location,
            "skills": skills,
            "experience": experience,
            "keywords": keywords
        }
    
    def _extract_role(self, tokens: list, normalized: str) -> str:
        """Extract the job role from query."""
        # Look for role keywords
        for i, token in enumerate(tokens):
            if token in self.ROLE_KEYWORDS:
                # Get context (previous word if exists)
                if i > 0:
                    return f"{tokens[i-1]} {token}"
                return token
        
        # Fallback: use first 3 tokens as role
        return " ".join(tokens[:3]) if tokens else "general position"
    
    def _extract_skills(self, tokens: list, normalized: str) -> list:
        """Extract skills from query."""
        skills = []
        for skill in self.SKILL_KEYWORDS:
            if skill in normalized:
                skills.append(skill)
        return skills[:5]  # Limit to 5 skills
    
    def _extract_location(self, tokens: list, normalized: str) -> str:
        """Extract location from query."""
        if 'san francisco' in normalized or 'sf' in normalized:
            return "San Francisco"
        if 'new york' in normalized or 'nyc' in normalized:
            return "New York"
            
        for loc in self.LOCATION_KEYWORDS:
            if loc in normalized:
                return loc.title()
        return "Remote"  # Default
    
    def _extract_experience(self, normalized: str) -> str:
        """Extract experience level from query."""
        import re
        # Look for patterns like "5+", "3+ years", "senior", "junior"
        exp_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)?', normalized)
        if exp_match:
            years = int(exp_match.group(1))
            if years >= 7:
                return "Senior"
            elif years >= 3:
                return "Mid-Level"
            else:
                return "Junior"
        
        if 'senior' in normalized or 'sr' in normalized:
            return "Senior"
        elif 'junior' in normalized or 'jr' in normalized:
            return "Junior"
        elif 'lead' in normalized or 'principal' in normalized:
            return "Lead"
        
        return "Mid-Level"  # Default

# Global instance for async usage
query_parser = AsyncQueryParser()
