"""
Regression Test: total_leads_found API Contract
Verifies that the API never returns total_leads_found=0 when leads exist.
"""
import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTotalLeadsFoundContract:
    """Tests for total_leads_found API contract integrity."""

    @pytest.mark.asyncio
    async def test_total_leads_found_matches_raw_leads(self):
        """total_leads_found must equal raw_leads_found from ExecutionReport."""
        from app.services.pipeline import RecruiterPipeline
        
        pipeline = RecruiterPipeline()
        await pipeline.initialize()
        
        result = await pipeline.process_recruiter_query(
            "Senior Python Developer San Francisco",
            recruiter_id="contract-test-001"
        )
        
        # Get values
        total_leads_found = result.get("total_leads_found")
        leads_count = len(result.get("leads", []))
        execution_report = result.get("execution_report_dto")
        
        # Assert leads exist
        assert leads_count > 0, "Test requires leads to be generated"
        
        # Assert total_leads_found equals raw_leads_found
        if execution_report:
            assert total_leads_found == execution_report.raw_leads_found, \
                f"total_leads_found ({total_leads_found}) != raw_leads_found ({execution_report.raw_leads_found})"
        
        # Assert contract invariant: leads > 0 implies total > 0
        assert total_leads_found > 0, \
            f"CONTRACT VIOLATION: leads exist ({leads_count}) but total_leads_found=0"
        
        # Assert total >= leads
        assert total_leads_found >= leads_count, \
            f"total_leads_found ({total_leads_found}) < len(leads) ({leads_count})"

    @pytest.mark.asyncio
    async def test_orchestration_summary_populated(self):
        """orchestration_summary must be populated with ExecutionReport data."""
        from app.services.pipeline import RecruiterPipeline
        
        pipeline = RecruiterPipeline()
        await pipeline.initialize()
        
        result = await pipeline.process_recruiter_query(
            "Machine Learning Engineer",
            recruiter_id="contract-test-002"
        )
        
        summary = result.get("orchestration_summary")
        assert summary is not None, "orchestration_summary must not be None"
        
        # Check canonical fields
        assert "raw_leads_found" in summary, "raw_leads_found missing from summary"
        assert summary["raw_leads_found"] > 0, "raw_leads_found must be > 0 when leads exist"
        
    @pytest.mark.asyncio  
    async def test_contract_invariant_enforcement(self):
        """Verify contract invariant is enforced: len(leads)>0 implies total_leads_found>0."""
        from app.services.pipeline import RecruiterPipeline
        
        pipeline = RecruiterPipeline()
        await pipeline.initialize()
        
        result = await pipeline.process_recruiter_query(
            "Data Scientist",
            recruiter_id="contract-test-003"
        )
        
        leads_count = len(result.get("leads", []))
        total_leads_found = result.get("total_leads_found", 0)
        
        if leads_count > 0:
            assert total_leads_found > 0, \
                "INVARIANT VIOLATED: leads exist but total_leads_found is 0"

    @pytest.mark.asyncio
    async def test_search_orchestrator_report_integrity(self):
        """ExecutionReport from SearchOrchestrator must have correct raw_leads_found."""
        from app.search.search_orchestrator import SearchOrchestrator
        
        orch = SearchOrchestrator()
        result = await orch.orchestrate(
            "Backend Developer",
            {"intelligence": {"role": "Backend Developer"}, "signals": {}}
        )
        
        report = result.get("execution_report")
        leads = result.get("leads", [])
        total_count = result.get("total_count")
        
        # Assertions
        assert report is not None, "ExecutionReport must exist"
        assert report.raw_leads_found == total_count, \
            f"raw_leads_found ({report.raw_leads_found}) != total_count ({total_count})"
        assert len(leads) <= report.raw_leads_found, \
            "More leads returned than raw_leads_found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
