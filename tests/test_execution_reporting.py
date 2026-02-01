import pytest
import asyncio
from app.search.search_orchestrator import SearchOrchestrator, ExecutionReport
from app.services.pipeline import recruiter_pipeline
from app.database import SessionLocal, ExecutionReport as DBExecutionReport
from app.config import settings

@pytest.mark.asyncio
async def test_execution_report_structure():
    """Verify ExecutionReport DTO structure match."""
    settings.agent.enable_mock_sources = True
    orch = SearchOrchestrator()
    result = await orch.orchestrate("python developer", {"intelligence": {}, "signals": {}})
    
    report = result.get("execution_report")
    assert isinstance(report, ExecutionReport)
    assert report.query == "python developer"
    assert report.raw_leads_found > 0
    assert report.ranked_leads_count > 0
    assert report.execution_time_ms > 0
    assert report.providers_called > 0
    assert report.execution_mode is not None

@pytest.mark.asyncio
async def test_pipeline_persistence():
    """Verify end-to-end flow: Orchestrator -> Pipeline -> DB Persistence."""
    # Ensure DB tables exist (if using in-memory or test DB, usually validation script handles this)
    # Here we rely on shared test env
    
    # Run Pipeline
    result = await recruiter_pipeline.process_recruiter_query("senior python dev")
    query_id = result["query_id"]
    
    # 1. Verify API Response Contract
    assert "orchestration_summary" in result
    summary = result["orchestration_summary"]
    assert summary["raw_leads_found"] > 0
    assert summary["providers_called"] > 0
    assert result["total_leads_found"] == summary["raw_leads_found"]
    
    # 2. Verify Database Persistence
    db = SessionLocal()
    try:
        report = db.query(DBExecutionReport).filter(DBExecutionReport.query_id == query_id).first()
        assert report is not None
        assert report.query_id == query_id
        assert report.raw_leads_found == summary["raw_leads_found"]
        assert report.providers_succeeded > 0
        assert report.leads_saved > 0 
        assert report.execution_mode in ["dev", "staging", "production"]
    finally:
        db.close()

@pytest.mark.asyncio
async def test_contract_integrity():
    """Verify strict invariant: len(leads) <= total_leads_found."""
    result = await recruiter_pipeline.process_recruiter_query("java architect")
    
    leads = result["leads"]
    total = result["total_leads_found"]
    
    # Strict contract
    assert len(leads) <= total
    assert total > 0 if len(leads) > 0 else True
    
    # Check that total reflects RAW count (usually much higher than 20 limit)
    # With mock data, we get ~5-10 leads usually, so easy to verify
    # If we had pagination limit 20 and found 5, total is 5.
    # If we found 100, total is 100, and len(leads) is 20.
    
    report = result["execution_report_dto"]
    assert report.raw_leads_found == total
