import pytest
import asyncio
from app.search.search_orchestrator import SearchOrchestrator
from app.config import settings, ExecutionMode

@pytest.mark.asyncio
async def test_orchestration_summary_present():
    """Verify orchestration_summary and strict metric contracts."""
    # Setup DEV mode
    settings.logging.mode = ExecutionMode.DEV
    settings.agent.enable_mock_sources = True
    
    orch = SearchOrchestrator()
    result = await orch.orchestrate("python developer", {"intelligence": {}, "signals": {}})
    
    # Check Summary Presence
    assert "orchestration_summary" in result
    summary = result["orchestration_summary"]
    
    # Check Fidelity Metrics
    assert summary["total_raw_leads"] > 0
    assert summary["total_normalized_leads"] > 0
    assert summary["total_ranked_leads"] > 0
    # Pre-truncation count contract
    assert summary["total_leads_found"] >= summary["total_ranked_leads"]
    
    # Check Provider Metrics
    assert summary["providers_called"] > 0
    assert summary["providers_succeeded"] > 0
    assert "provider_diagnostics" in summary
    
    # Check Timing
    assert summary["total_duration_ms"] > 0.0
    
@pytest.mark.asyncio
async def test_provider_telemetry_attached():
    """Verify granular provider telemetry in both summary and metrics."""
    settings.agent.enable_mock_sources = True
    orch = SearchOrchestrator()
    result = await orch.orchestrate("python developer", {"intelligence": {}, "signals": {}})
    
    # 1. In Metrics
    assert "metrics" in result
    diagnostics = result["metrics"]["provider_diagnostics"]
    assert "MockStartupDB" in diagnostics
    assert diagnostics["MockStartupDB"]["status"] == "success"
    assert diagnostics["MockStartupDB"]["latency_ms"] > 0
    assert diagnostics["MockStartupDB"]["leads_found"] > 0

    # 2. In Summary
    summary_diag = result["orchestration_summary"]["provider_diagnostics"]
    assert summary_diag == diagnostics

@pytest.mark.asyncio
async def test_total_leads_found_fidelity():
    """Verify total_leads_found is never 0 if leads exist (Correction Contract)."""
    settings.agent.enable_mock_sources = True
    orch = SearchOrchestrator()
    result = await orch.orchestrate("python developer", {"intelligence": {}, "signals": {}})
    
    leads = result["leads"]
    total = result["total_count"]
    
    assert len(leads) > 0
    assert total > 0
    assert total >= len(leads) # Logic check

@pytest.mark.asyncio
async def test_execution_mode_logging_config():
    """Verify LoggingSettings respects ExecutionMode."""
    # This is a config test
    from app.config import LoggingSettings
    
    # DEV defaults
    dev_settings = LoggingSettings(mode=ExecutionMode.DEV)
    assert dev_settings.app_log_path == "logs/app.log"
    
    # PROD defaults
    prod_settings = LoggingSettings(mode=ExecutionMode.PRODUCTION)
    # Paths remain defaults but usage differs in logic
    assert prod_settings.mode == ExecutionMode.PRODUCTION
