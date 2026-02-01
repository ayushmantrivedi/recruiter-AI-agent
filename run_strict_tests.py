
import sys
import os
import asyncio
import traceback

# Add app to path
sys.path.append(os.getcwd())

from tests.test_strict_compliance import (
    test_determinism,
    test_sensitivity,
    test_location_competition,
    test_intent_control,
    test_broken_grammar,
    test_aliases,
    test_noise,
    test_e2e_api_contract,
    test_async_completion_guarantee,
    test_schema_integrity,
    test_transaction_atomicity
)

def run_sync_test(test_func):
    try:
        test_func()
        print(f"✅ {test_func.__name__} PASSED")
        return True
    except Exception as e:
        print(f"❌ {test_func.__name__} FAILED: {str(e)}")
        traceback.print_exc()
        return False

async def run_async_test(test_func):
    try:
        await test_func()
        print(f"✅ {test_func.__name__} PASSED")
        return True
    except Exception as e:
        print(f"❌ {test_func.__name__} FAILED: {str(e)}")
        traceback.print_exc()
        return False

    with open("test_results.txt", "w", encoding="utf-8") as f:
        def log(msg):
            print(msg)
            f.write(msg + "\n")

        log("Running STRICT COMPLIANCE tests...")
        
        passed = 0
        total = 0
        
        # Phase 1
        total += 1; passed += 1 if run_sync_test(test_determinism) else 0
        total += 1; passed += 1 if run_sync_test(test_sensitivity) else 0
        total += 1; passed += 1 if run_sync_test(test_location_competition) else 0
        total += 1; passed += 1 if run_sync_test(test_intent_control) else 0
        
        # Phase 2
        total += 1; passed += 1 if run_sync_test(test_broken_grammar) else 0
        total += 1; passed += 1 if run_sync_test(test_aliases) else 0
        total += 1; passed += 1 if run_sync_test(test_noise) else 0
        
        # Phase 3
        total += 1; passed += 1 if run_sync_test(test_e2e_api_contract) else 0
        
        total += 1; passed += 1 if await run_async_test(test_async_completion_guarantee) else 0
        
        # Phase 4
        try:
            total += 1; passed += 1 if run_sync_test(test_schema_integrity) else 0
        except: 
            log("Skipping schema integrity due to import issues if any")
            
        try:
            total += 1; passed += 1 if run_sync_test(test_transaction_atomicity) else 0
        except:
            log("Skipping atomicity due to session issues if any")

        log(f"\n{passed}/{total} Strict Tests Passed")
        
        if passed == total:
            log("ALL STRICT TESTS PASSED")
            sys.exit(0)
        else:
            log("SOME TESTS FAILED")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
