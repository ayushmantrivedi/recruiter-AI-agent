"""
Platform Unification Test Suite

Verifies that the platform has a single, deterministic execution path
with no split-brain conditions. This is the core stability contract.
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSingleExecutionPath:
    """Tests for unified execution path."""

    @pytest.mark.asyncio
    async def test_sync_and_async_paths_use_same_pipeline(self):
        """Both sync and async paths should use RecruiterPipeline.process_recruiter_query."""
        from app.routes.recruiter import process_query_background
        from app.services.pipeline import recruiter_pipeline
        
        # Check that process_query_background calls the unified pipeline
        # by inspecting its source code (since we can't easily mock at import time)
        import inspect
        source = inspect.getsource(process_query_background)
        
        # Verify the async path calls the unified pipeline method
        assert "recruiter_pipeline.process_recruiter_query" in source
        # Verify the legacy split-brain function is NOT called
        assert "_execute_pipeline_with_checkpoint" not in source
    
    def test_legacy_checkpoint_function_removed(self):
        """The legacy _execute_pipeline_with_checkpoint should not exist."""
        from app.routes import recruiter
        
        # The function should not exist as a callable
        assert not hasattr(recruiter, '_execute_pipeline_with_checkpoint') or \
               not callable(getattr(recruiter, '_execute_pipeline_with_checkpoint', None))
    
    @pytest.mark.asyncio
    async def test_execution_report_always_created(self):
        """ExecutionReport should always be created regardless of path."""
        from app.search.search_orchestrator import SearchOrchestrator
        
        # Create fresh orchestrator
        orchestrator = SearchOrchestrator()
        
        result = await orchestrator.orchestrate(
            "Senior Python Developer",
            {"intelligence": {"role": "Python Developer"}, "signals": {}}
        )
        
        # Verify ExecutionReport is present
        assert "execution_report" in result
        report = result["execution_report"]
        
        # Verify it has the canonical fields
        assert hasattr(report, 'raw_leads_found')
        assert hasattr(report, 'normalized_leads')
        assert hasattr(report, 'ranked_leads_count')
        assert hasattr(report, 'providers_called')
        assert hasattr(report, 'execution_time_ms')


class TestStartupIntegrity:
    """Tests for boot-time validation."""

    def test_verify_search_providers_exists(self):
        """verify_search_providers should be defined in main.py."""
        from app import main
        
        assert hasattr(main, 'verify_search_providers')
        assert callable(main.verify_search_providers)
    
    def test_verify_database_schema_checks_execution_reports(self):
        """verify_database_schema should check for execution_reports table."""
        from app import main
        import inspect
        
        source = inspect.getsource(main.verify_database_schema)
        assert 'execution_reports' in source
    
    def test_search_orchestrator_has_active_providers(self):
        """SearchOrchestrator should have active providers in DEV mode."""
        from app.search.search_orchestrator import SearchOrchestrator
        
        orchestrator = SearchOrchestrator()
        
        # Must have at least one provider
        assert len(orchestrator.sources) > 0

    def test_zero_providers_raises_error(self):
        """SearchOrchestrator should fail fast with zero providers."""
        from app.search.search_orchestrator import SearchOrchestrator
        
        with patch('app.config.settings') as mock_settings:
            mock_settings.logging.mode = MagicMock()
            mock_settings.logging.mode.value = "dev"
            mock_settings.agent.enable_arbeitnow = False
            mock_settings.agent.enable_github_jobs = False
            mock_settings.agent.enable_mock_sources = False
            
            with pytest.raises(RuntimeError, match="No search providers enabled"):
                SearchOrchestrator()


class TestExecutionConsistency:
    """Tests for consistent execution results."""

    @pytest.mark.asyncio
    async def test_total_leads_found_matches_raw_count(self):
        """total_leads_found should match raw_leads_found from ExecutionReport."""
        from app.services.pipeline import RecruiterPipeline
        
        pipeline = RecruiterPipeline()
        await pipeline.initialize()
        
        result = await pipeline.process_recruiter_query(
            "Machine Learning Engineer",
            recruiter_id="test-001"
        )
        
        if result.get("execution_report_dto"):
            report = result["execution_report_dto"]
            assert result["total_leads_found"] == report.raw_leads_found
    
    @pytest.mark.asyncio
    async def test_orchestration_summary_populated(self):
        """orchestration_summary should always be populated."""
        from app.services.pipeline import RecruiterPipeline
        
        pipeline = RecruiterPipeline()
        await pipeline.initialize()
        
        result = await pipeline.process_recruiter_query(
            "Data Scientist",
            recruiter_id="test-002"
        )
        
        assert "orchestration_summary" in result
        summary = result["orchestration_summary"]
        
        # Canonical fields from ExecutionReport
        assert "raw_leads_found" in summary or "providers_called" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
