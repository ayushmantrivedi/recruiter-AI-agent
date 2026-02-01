
import pytest
from app.intelligence.query_parser import QueryParser
from app.intelligence.intent_classifier import IntentClassifier
from app.intelligence.role_extractor import RoleExtractor
from app.intelligence.signal_engine import SignalEngine
from app.intelligence.intelligence_engine import IntelligenceEngine

# 1. Intent Tests
def test_intent_hiring():
    result = IntentClassifier.classify("Find AI engineers")
    assert result.intent == "HIRING"

def test_intent_salary():
    result = IntentClassifier.classify("What is ML salary")
    assert result.intent == "SALARY"

def test_intent_research():
    result = IntentClassifier.classify("Market trend for AI")
    assert result.intent == "RESEARCH"

# 2. Extraction Tests
def test_extraction_complex():
    query = "Find senior backend engineers in Pune with 4+ years"
    profile = RoleExtractor.extract(query)
    
    assert profile.role == "Backend Engineer"
    assert profile.location == "Pune"
    assert profile.experience == 4
    assert profile.seniority == "Senior"

# 3. Signal Ordering Test
@pytest.mark.asyncio
async def test_signal_ordering():
    # Urgently need senior AI engineers -> High pressure
    res1 = await IntelligenceEngine.process("Urgently need senior AI engineers")
    
    # Find junior frontend devs -> Lower pressure
    res2 = await IntelligenceEngine.process("Find junior frontend devs")
    
    assert res1.hiring_pressure > res2.hiring_pressure
    assert res1.role_scarcity > res2.role_scarcity

# 4. Stability Test
@pytest.mark.asyncio
async def test_stability():
    query = "Looking for Senior Data Scientist in Bangalore"
    first_result = await IntelligenceEngine.process(query)
    
    for _ in range(10):
        res = await IntelligenceEngine.process(query)
        assert res.hiring_pressure == first_result.hiring_pressure
        assert res.role_scarcity == first_result.role_scarcity
        assert res.market_difficulty == first_result.market_difficulty
        assert res.role == first_result.role

# 5. Boundary Test
@pytest.mark.asyncio
async def test_boundary_general():
    res = await IntelligenceEngine.process("hii")
    assert res.intent == "GENERAL"
    assert res.hiring_pressure < 0.2  # Should be low for general intent

# 6. Robustness Test
@pytest.mark.asyncio
async def test_robustness():
    res = await IntelligenceEngine.process("Looking 4 ML devs in Blr ASAP")
    assert res.intent == "HIRING" # "Looking"
    assert res.role == "ML Engineer" # "ML" maps to ML Engineer
    assert res.location == "Bangalore" # "Blr" maps to Bangalore
    
