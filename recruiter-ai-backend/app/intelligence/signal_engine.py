from .market_context import ROLE_SCARCITY, SENIORITY_DIFFICULTY, LOCATION_COMPETITION

class SignalEngine:
    @staticmethod
    def compute_signals(intent: str, role: str, seniority: str, location: str) -> dict:
        
        # Get base multipliers
        role_factor = ROLE_SCARCITY.get(role, 0.5)
        seniority_factor = SENIORITY_DIFFICULTY.get(seniority, 0.5)
        location_factor = LOCATION_COMPETITION.get(location, 0.5)
        
        # 1. Role Scarcity
        # Combined effect of role and seniority
        role_scarcity = min(0.99, role_factor * 0.8 + seniority_factor * 0.2)
        if seniority == "Lead" or seniority == "Principal":
             role_scarcity = min(0.99, role_scarcity + 0.1)

        # 2. Hiring Pressure
        # Dependent on Intent + Difficulty
        intent_weight = 0.3 # Base
        if intent == "HIRING":
            intent_weight = 0.9
        elif intent == "SALARY" or intent == "BENCHMARK":
            intent_weight = 0.5
        elif intent == "GENERAL":
            intent_weight = 0.0
        
        hiring_pressure = min(0.99, intent_weight * 0.7 + seniority_factor * 0.3)
        
        if intent == "GENERAL":
            hiring_pressure = min(0.1, hiring_pressure)
        
        # 3. Market Difficulty
        # Average of scarcity and location competition
        market_difficulty = (role_scarcity + location_factor) / 2
        
        # 4. Outsourcing Likelihood
        # Heuristic: High urgency/difficulty -> Higher outsourcing
        outsourcing_likelihood = 0.3 # Base
        if hiring_pressure > 0.7 or market_difficulty > 0.7:
            outsourcing_likelihood = 0.7
        if seniority == "Junior":
            outsourcing_likelihood = 0.2
            
            
        return {
            "hiring_pressure": round(hiring_pressure, 2),
            "role_scarcity": round(role_scarcity, 2),
            "outsourcing_likelihood": round(outsourcing_likelihood, 2),
            "market_difficulty": round(market_difficulty, 2)
        }
