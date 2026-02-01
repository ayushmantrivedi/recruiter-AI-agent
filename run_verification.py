
import sys
import os

# Add app to path
sys.path.append(os.getcwd())

from tests.test_intelligence_engine import (
    test_intent_hiring,
    test_intent_salary,
    test_intent_research,
    test_extraction_complex,
    test_signal_ordering,
    test_stability,
    test_boundary_general,
    test_robustness
)

def run_test(test_func):
    try:
        test_func()
        print(f"✅ {test_func.__name__} PASSED")
        return True
    except AssertionError as e:
        print(f"❌ {test_func.__name__} FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ {test_func.__name__} ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Running verification tests...")
    tests = [
        test_intent_hiring,
        test_intent_salary,
        test_intent_research,
        test_extraction_complex,
        test_signal_ordering,
        test_stability,
        test_boundary_general,
        test_robustness
    ]
    
    passed = 0
    for test in tests:
        if run_test(test):
            passed += 1
            
    print(f"\n{passed}/{len(tests)} Tests Passed")
    
    if passed == len(tests):
        print("ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
