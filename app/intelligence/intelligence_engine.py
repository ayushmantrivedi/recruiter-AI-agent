from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from .query_parser import QueryParser
from .intent_classifier import IntentClassifier
from .role_extractor import RoleExtractor
from .signal_engine import SignalEngine

@dataclass
class IntelligenceResult:
    intent: str
    role: str
    skills: List[str]
    experience: int
    seniority: str
    location: str
    hiring_pressure: float
    role_scarcity: float
    outsourcing_likelihood: float
    market_difficulty: float
    
    def dict(self) -> Dict[str, Any]:
        return asdict(self)

class IntelligenceEngine:
    @staticmethod
    async def process(query_text: str) -> IntelligenceResult:
        # 1. Parse (using global instance)
        from .query_parser import query_parser
        parsed_dict = await query_parser.parse(query_text)
        
        # 2. Intent (mock implementation for now based on parsed role)
        role = parsed_dict.get("role", "unknown")
        intent = "hiring" if role else "general"
        
        # 3. Extract entities
        # Map dictionary back to what RoleExtractor expects or just use dictionary directly
        # For now, let's just use the parsed data directly to construct profile
        
        # 4. Compute Signals
        signals = SignalEngine.compute_signals(
            intent=intent,
            role=role,
            seniority=parsed_dict.get("experience", "Unknown"), # simplified mapping
            location=parsed_dict.get("location", "Remote")
        )
        
        return IntelligenceResult(
            intent=intent,
            role=role,
            skills=parsed_dict.get("skills", []),
            experience=5 if parsed_dict.get("experience") else 1, # fast fallback
            seniority=parsed_dict.get("experience", "Mid-Level"),
            location=parsed_dict.get("location", "Remote"),
            hiring_pressure=signals["hiring_pressure"],
            role_scarcity=signals["role_scarcity"],
            outsourcing_likelihood=signals["outsourcing_likelihood"],
            market_difficulty=signals["market_difficulty"]
        )

