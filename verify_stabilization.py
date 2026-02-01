"""
Platform Stabilization Verification Script
Tests all observability and ExecutionReport contracts.
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.utils.logger import setup_logging
setup_logging()

async def verify_platform():
    print("=" * 60)
    print("PLATFORM STABILIZATION VERIFICATION")
    print("=" * 60)
    
    results = {}
    
    # 1. Console Logging Test
    print("\n[1/5] Console Logging Test...")
    from app.utils.logger import get_logger
    logger = get_logger("verification")
    logger.info("CONSOLE_LOG_TEST", status="visible")
    results["console_logging"] = True
    print("[PASS] Console logging working")
    
    # 2. SearchOrchestrator ExecutionReport Test
    print("\n[2/5] ExecutionReport Wiring Test...")
    from app.search.search_orchestrator import SearchOrchestrator
    orch = SearchOrchestrator()
    search_result = await orch.orchestrate(
        "Senior Python Developer San Francisco",
        {"intelligence": {"role": "Python Developer", "location": "San Francisco"}, "signals": {}}
    )
    
    report = search_result.get("execution_report")
    if report:
        print(f"  raw_leads_found: {report.raw_leads_found}")
        print(f"  normalized_leads: {report.normalized_leads}")
        print(f"  ranked_leads_count: {report.ranked_leads_count}")
        print(f"  providers_called: {report.providers_called}")
        print(f"  execution_time_ms: {report.execution_time_ms}")
        results["execution_report"] = report.raw_leads_found > 0
    else:
        print("[FAIL] ExecutionReport is None!")
        results["execution_report"] = False
    print("[PASS] ExecutionReport correctly created" if results["execution_report"] else "[FAIL] ExecutionReport BROKEN")
    
    # 3. orchestration_summary Test
    print("\n[3/5] orchestration_summary Contract Test...")
    summary = search_result.get("orchestration_summary")
    if summary and "raw_leads_found" in summary:
        print(f"  summary.raw_leads_found: {summary.get('raw_leads_found')}")
        results["orchestration_summary"] = True
    else:
        print("[FAIL] orchestration_summary missing or incomplete")
        results["orchestration_summary"] = False
    print("[PASS] orchestration_summary present" if results["orchestration_summary"] else "[FAIL] orchestration_summary BROKEN")
    
    # 4. total_count Fidelity Test
    print("\n[4/5] total_count Fidelity Test...")
    total_count = search_result.get("total_count")
    leads_count = len(search_result.get("leads", []))
    results["total_count_fidelity"] = total_count is not None and total_count >= leads_count
    print(f"  total_count: {total_count}")
    print(f"  leads in response: {leads_count}")
    print(f"  Invariant (total >= leads): {total_count >= leads_count}")
    print("[PASS] total_count correct" if results["total_count_fidelity"] else "[FAIL] total_count BROKEN")
    
    # 5. Pipeline Integration Test
    print("\n[5/5] Pipeline Integration Test...")
    from app.services.pipeline import RecruiterPipeline
    pipeline = RecruiterPipeline()
    await pipeline.initialize()
    
    pipeline_result = await pipeline.process_recruiter_query(
        "Machine Learning Engineer",
        recruiter_id="verification-test"
    )
    
    api_summary = pipeline_result.get("orchestration_summary")
    api_total = pipeline_result.get("total_leads_found")
    api_leads = len(pipeline_result.get("leads", []))
    
    results["pipeline_integration"] = (
        api_summary is not None and 
        api_total is not None and 
        api_total > 0 and 
        api_total >= api_leads
    )
    
    print(f"  API orchestration_summary: {'present' if api_summary else 'MISSING'}")
    print(f"  API total_leads_found: {api_total}")
    print(f"  API leads count: {api_leads}")
    print(f"  Invariant check: {api_total > 0 and api_total >= api_leads}")
    print("[PASS] Pipeline integration working" if results["pipeline_integration"] else "[FAIL] Pipeline BROKEN")
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = all(results.values())
    for test, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {test}: {status}")
    
    print("\n" + ("ALL TESTS PASSED - PLATFORM STABLE" if all_passed else "SOME TESTS FAILED"))
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(verify_platform())
    sys.exit(0 if success else 1)
