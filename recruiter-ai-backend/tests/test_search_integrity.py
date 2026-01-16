import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.search.search_orchestrator import SearchOrchestrator
from app.config import settings, SearchMode

@pytest.mark.asyncio
async def test_startup_fails_with_no_providers():
    """Verify that SearchOrchestrator raises RuntimeError if no provider is enabled."""
    # Temporarily disable all providers
    original_mocks = settings.agent.enable_mock_sources
    original_arbeitnow = settings.agent.enable_arbeitnow
    original_github = settings.agent.enable_github_jobs
    
    settings.agent.enable_mock_sources = False
    settings.agent.enable_arbeitnow = False
    settings.agent.enable_github_jobs = False
    
    try:
        with pytest.raises(RuntimeError) as excinfo:
            SearchOrchestrator()
        assert "CRITICAL: No search providers enabled" in str(excinfo.value)
    finally:
        # Restore settings
        settings.agent.enable_mock_sources = original_mocks
        settings.agent.enable_arbeitnow = original_arbeitnow
        settings.agent.enable_github_jobs = original_github

@pytest.mark.asyncio
async def test_search_mode_provider_logic():
    """Verify SearchMode validation logic (via config)."""
    # This tests the Model Validator in config.py
    # We can't easily re-instantiate settings here without reloading env, 
    # but we can verify the logic by manually calling the validator or trusting pydantic.
    # Instead, let's verify SearchOrchestrator respects flags.
    
    # 1. Enable ONLY Mocks
    settings.agent.enable_mock_sources = True
    settings.agent.enable_arbeitnow = False
    settings.agent.enable_github_jobs = False
    
    orch = SearchOrchestrator()
    provider_names = [s.__class__.__name__ for s in orch.sources]
    assert "MockStartupDB" in provider_names
    assert "MockJobBoard" not in provider_names
    
    # 2. Enable ONLY Public APIs
    settings.agent.enable_mock_sources = False
    settings.agent.enable_arbeitnow = True
    orch2 = SearchOrchestrator()
    provider_names2 = [s.__class__.__name__ for s in orch2.sources]
    assert "MockJobBoard" in provider_names2
    assert "MockStartupDB" not in provider_names2


@pytest.mark.asyncio
async def test_telemetry_generation():
    """Verify that telemetry is generated and exposed."""
    # Enable mocks
    settings.agent.enable_mock_sources = True
    settings.agent.enable_arbeitnow = False
    
    orch = SearchOrchestrator()
    
    # Run orchestrate
    result = await orch.orchestrate("python developer", {"intelligence": {}, "signals": {}})
    
    assert "metrics" in result
    metrics = result["metrics"]
    assert "provider_diagnostics" in metrics
    diagnostics = metrics["provider_diagnostics"]
    
    # Check if we have entries
    assert "MockStartupDB" in diagnostics
    assert diagnostics["MockStartupDB"]["status"] == "success"
    assert "latency_ms" in diagnostics["MockStartupDB"]
    assert "leads_found" in diagnostics["MockStartupDB"]
