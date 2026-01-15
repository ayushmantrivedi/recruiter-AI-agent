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
    def process(query_text: str) -> IntelligenceResult:
        # 1. Parse
        parsed = QueryParser.parse(query_text)
        
        # 2. Intent
        intent_res = IntentClassifier.classify(parsed.normalized)
        
        # 3. Extract entities
        profile = RoleExtractor.extract(parsed.normalized)
        
        # 4. Compute Signals
        signals = SignalEngine.compute_signals(
            intent=intent_res.intent,
            role=profile.role,
            seniority=profile.seniority,
            location=profile.location
        )
        
        return IntelligenceResult(
            intent=intent_res.intent,
            role=profile.role,
            skills=profile.skills,
            experience=profile.experience,
            seniority=profile.seniority,
            location=profile.location,
            hiring_pressure=signals["hiring_pressure"],
            role_scarcity=signals["role_scarcity"],
            outsourcing_likelihood=signals["outsourcing_likelihood"],
            market_difficulty=signals["market_difficulty"]
        )
