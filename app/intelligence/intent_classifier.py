from dataclasses import dataclass
from typing import List

@dataclass
class IntentResult:
    intent: str
    confidence: float

class IntentClassifier:
    
    INTENT_KEYWORDS = {
        "HIRING": ["find", "hire", "need", "looking", "recruit", "urgent", "urgently", "want"],
        "SALARY": ["salary", "ctc", "pay", "compensation", "package"],
        "RESEARCH": ["market", "trend", "how many", "availability", "pool"],
        "BENCHMARK": ["compare", "benchmark", "vs", "versus"]
    }

    @staticmethod
    def classify(normalized_text: str) -> IntentResult:
        """
        Rule-based intent classification.
        """
        text = normalized_text.lower()
        
        for intent, keywords in IntentClassifier.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return IntentResult(intent=intent, confidence=1.0)
                    
        return IntentResult(intent="GENERAL", confidence=1.0)
