
import sys
import os
sys.path.append(os.getcwd())

from app.intelligence.intelligence_engine import IntelligenceEngine

def check(name, condition):
    if condition:
        print(f"✅ {name} PASSED")
    else:
        print(f"❌ {name} FAILED")
        sys.exit(1)

def run_tests():
    print("Starting Strict Phase 1-2 Tests...")
    
    # Test 1: Determinism
    q = "Urgently need senior AI engineers in Bangalore"
    res1 = IntelligenceEngine.process(q)
    res2 = IntelligenceEngine.process(q)
    check("Determinism", res1.hiring_pressure == res2.hiring_pressure and res1.role == res2.role)

    # Test 2: Sensitivity
    r1 = IntelligenceEngine.process("Find junior frontend developers in Jaipur")
    r2 = IntelligenceEngine.process("Find senior frontend developers in Jaipur")
    check("Sensitivity", r2.hiring_pressure > r1.hiring_pressure)

    # Test 3: Location
    bangalore = IntelligenceEngine.process("Find AI engineers in Bangalore")
    indore = IntelligenceEngine.process("Find AI engineers in Indore")
    check("Location Difficulty", bangalore.market_difficulty > indore.market_difficulty)

    # Test 4: Intent
    hiring = IntelligenceEngine.process("Find ML engineers in Pune")
    salary = IntelligenceEngine.process("What is ML engineer salary in Pune")
    check("Intent Control", hiring.intent == "HIRING" and salary.intent == "SALARY" and hiring.hiring_pressure > salary.hiring_pressure)

    # Test 5: Broken Grammar
    broken = IntelligenceEngine.process("need 4 ai dev blr asap")
    check("Broken Grammar", "AI" in broken.role or "ML" in broken.role)
    check("Broken Grammar Loc", broken.location == "Bangalore")

    # Test 6: Aliases
    aliases = IntelligenceEngine.process("Looking 4 ML devs in Blr")
    check("Aliases", aliases.role == "ML Engineer" and aliases.location == "Bangalore")

    # Test 7: Noise
    noise = IntelligenceEngine.process("Hey buddy pls help me find some good senior backend engineers in delhi ok?")
    check("Noise", noise.role == "Backend Engineer" and noise.location == "Delhi" and noise.seniority == "Senior")

    print("ALL PHASE 1-2 STRICT TESTS PASSED")

if __name__ == "__main__":
    run_tests()
