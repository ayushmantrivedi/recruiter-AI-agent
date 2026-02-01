"""
Tests for the Recruiter API endpoints.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from app.main import app


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


class TestAPIHealth:
    """Test health check endpoints."""

    def test_health_endpoint(self, client):
        """Test basic health endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data

    def test_api_recruiter_health_endpoint(self, client):
        """Test recruiter-specific health endpoint."""
        response = client.get("/api/recruiter/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestAPIQuerySubmission:
    """Test query submission and processing."""

    @patch('app.routes.recruiter.recruiter_pipeline')
    def test_submit_query_success(self, mock_pipeline, client):
        """Test successful query submission."""
        # Mock the pipeline to return a successful result
        mock_pipeline.process_recruiter_query = AsyncMock(return_value={
            "query_id": "test-123",
            "status": "completed",
            "original_query": "Find Python developers",
            "total_leads_found": 2,
            "processing_time": 1.5,
            "leads": []
        })

        response = client.post("/api/recruiter/query", json={
            "query": "Find Python developers",
            "recruiter_id": "test-1"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["query_id"] == "test-123"
        assert data["status"] == "completed"
        assert data["original_query"] == "Find Python developers"

    @patch('app.routes.recruiter.recruiter_pipeline')
    def test_submit_query_background_processing(self, mock_pipeline, client):
        """Test query submission with background processing for longer queries."""
        # Mock the pipeline
        mock_pipeline.process_recruiter_query = AsyncMock()

        response = client.post("/api/recruiter/query", json={
            "query": "Find senior Python developers with 5+ years experience in San Francisco",
            "recruiter_id": "test-1"
        })

        assert response.status_code == 200
        data = response.json()
        assert "query_id" in data
        assert data["status"] == "processing"
        assert data["original_query"] == "Find senior Python developers with 5+ years experience in San Francisco"

    def test_submit_query_missing_fields(self, client):
        """Test query submission with missing required fields."""
        response = client.post("/api/recruiter/query", json={})

        assert response.status_code == 422  # Validation error

    def test_submit_query_invalid_data(self, client):
        """Test query submission with invalid data."""
        response = client.post("/api/recruiter/query", json={
            "query": "",  # Too short
            "recruiter_id": "test-1"
        })

        assert response.status_code == 422  # Validation error

    @patch('app.routes.recruiter.recruiter_pipeline')
    def test_submit_query_pipeline_error(self, mock_pipeline, client):
        """Test query submission when pipeline fails."""
        # Mock the pipeline to raise an exception
        mock_pipeline.process_recruiter_query = AsyncMock(side_effect=Exception("Pipeline error"))

        response = client.post("/api/recruiter/query", json={
            "query": "Find Python developers"
        })

        assert response.status_code == 500
        data = response.json()
        assert "Query processing failed" in data["message"]


class TestAPIQueryStatus:
    """Test query status retrieval."""

    @patch('app.routes.recruiter.recruiter_pipeline')
    def test_get_query_status_completed(self, mock_pipeline, client):
        """Test getting status of completed query."""
        mock_pipeline.get_query_status = AsyncMock(return_value={
            "query_id": "test-123",
            "status": "completed",
            "original_query": "Find Python developers",
            "total_leads_found": 3,
            "processing_time": 2.5,
            "leads": [
                {
                    "company": "TechCorp",
                    "score": 0.85,
                    "confidence": 0.9,
                    "evidence_count": 5,
                    "reasons": ["Strong match"]
                }
            ]
        })

        response = client.get("/api/recruiter/query/test-123")

        assert response.status_code == 200
        data = response.json()
        assert data["query_id"] == "test-123"
        assert data["status"] == "completed"
        assert data["total_leads_found"] == 3
        assert len(data["leads"]) == 1

    @patch('app.routes.recruiter.recruiter_pipeline')
    def test_get_query_status_processing(self, mock_pipeline, client):
        """Test getting status of processing query."""
        mock_pipeline.get_query_status = AsyncMock(return_value={
            "query_id": "test-123",
            "status": "processing",
            "original_query": "Find Python developers"
        })

        response = client.get("/api/recruiter/query/test-123")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"

    @patch('app.routes.recruiter.recruiter_pipeline')
    def test_get_query_status_not_found(self, mock_pipeline, client):
        """Test getting status of non-existent query."""
        mock_pipeline.get_query_status = AsyncMock(return_value=None)

        response = client.get("/api/recruiter/query/nonexistent-123")

        assert response.status_code == 404
        data = response.json()
        assert "Query not found" in data["detail"]

    @patch('app.routes.recruiter.recruiter_pipeline')
    def test_get_query_status_pipeline_error(self, mock_pipeline, client):
        """Test getting status when pipeline fails."""
        mock_pipeline.get_query_status = AsyncMock(side_effect=Exception("Pipeline error"))

        response = client.get("/api/recruiter/query/test-123")

        assert response.status_code == 500
        data = response.json()
        assert "Failed to retrieve query results" in data["detail"]


class TestAPIDataValidation:
    """Test API data validation."""

    def test_query_request_validation(self, client):
        """Test QueryRequest model validation."""
        # Valid request
        response = client.post("/api/recruiter/query", json={
            "query": "Find Python developers with 3+ years experience",
            "recruiter_id": "test-1"
        })
        # Should not fail validation (even if pipeline fails)
        assert response.status_code in [200, 500]

        # Invalid: query too short
        response = client.post("/api/recruiter/query", json={
            "query": "Hi",
            "recruiter_id": "test-1"
        })
        assert response.status_code == 422

        # Invalid: query too long
        long_query = "Find " + "developers " * 100
        response = client.post("/api/recruiter/query", json={
            "query": long_query,
            "recruiter_id": "test-1"
        })
        assert response.status_code == 422


class TestAPIErrorHandling:
    """Test API error handling."""

    def test_invalid_json(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            "/api/recruiter/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_unsupported_content_type(self, client):
        """Test handling of unsupported content types."""
        response = client.post(
            "/api/recruiter/query",
            data="query=Find Python developers",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        assert response.status_code == 422

    def test_method_not_allowed(self, client):
        """Test handling of incorrect HTTP methods."""
        response = client.put("/api/recruiter/query", json={"query": "test"})

        assert response.status_code == 405


class TestAPIRateLimiting:
    """Test API rate limiting (if implemented)."""

    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        # This would test rate limiting if implemented
        # For now, just verify basic functionality
        responses = []
        for i in range(3):
            response = client.get("/api/recruiter/health")
            responses.append(response.status_code)

        assert all(code == 200 for code in responses)


class TestAPIMetrics:
    """Test API metrics endpoints."""

    def test_metrics_endpoints_exist(self, client):
        """Test that metrics endpoints exist and return data."""
        endpoints = [
            "/api/recruiter/metrics/dashboard",
            "/api/recruiter/metrics/usage",
            "/api/recruiter/metrics/performance",
            "/api/recruiter/metrics"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should return some response (may be empty data)
            assert response.status_code in [200, 500]  # 500 if DB not available in tests


@pytest.mark.asyncio
async def test_concurrent_job_execution():
    """Stress test: Submit multiple jobs concurrently and verify completion."""
    import asyncio
    import time

    # Test configuration
    CONCURRENT_JOBS = 5
    TEST_TIMEOUT = 60  # seconds

    client = TestClient(app)
    job_ids = []

    # Submit multiple jobs concurrently
    start_time = time.time()

    async def submit_job(job_num: int):
        """Submit a single job."""
        query = f"Find Python developers job {job_num}"
        response = client.post("/api/recruiter/query", json={
            "query": query,
            "recruiter_id": f"test-user-{job_num}"
        })

        assert response.status_code == 200
        data = response.json()
        assert "query_id" in data
        return data["query_id"], query

    # Submit all jobs concurrently
    print(f"Submitting {CONCURRENT_JOBS} concurrent jobs...")
    submit_tasks = [submit_job(i) for i in range(CONCURRENT_JOBS)]
    submit_results = await asyncio.gather(*submit_tasks)

    job_ids = [job_id for job_id, _ in submit_results]
    print(f"Submitted jobs: {job_ids}")

    # Wait for all jobs to complete
    async def wait_for_completion(job_id: str, timeout_seconds: int = TEST_TIMEOUT):
        """Wait for a job to complete."""
        start_poll = time.time()

        while time.time() - start_poll < timeout_seconds:
            response = client.get(f"/api/recruiter/query/{job_id}")
            assert response.status_code == 200

            data = response.json()
            status = data.get("status")

            if status == "completed":
                return True, data
            elif status == "failed":
                return False, data

            # Wait before polling again
            await asyncio.sleep(0.5)

        # Timeout reached
        return False, {"status": "timeout", "query_id": job_id}

    # Poll all jobs concurrently
    print("Waiting for all jobs to complete...")
    poll_tasks = [wait_for_completion(job_id) for job_id in job_ids]
    poll_results = await asyncio.gather(*poll_tasks)

    # Analyze results
    completed_jobs = 0
    failed_jobs = 0
    timeout_jobs = 0

    for i, (success, result) in enumerate(poll_results):
        job_id = job_ids[i]
        if success and result.get("status") == "completed":
            completed_jobs += 1
            print(f"✅ Job {job_id} completed successfully")
        elif not success and result.get("status") == "failed":
            failed_jobs += 1
            print(f"❌ Job {job_id} failed: {result.get('error', 'unknown error')}")
        else:
            timeout_jobs += 1
            print(f"⏰ Job {job_id} timed out")

    # Verify results
    total_time = time.time() - start_time
    print(f"\nTest Results:")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Completed: {completed_jobs}")
    print(f"Failed: {failed_jobs}")
    print(f"Timeout: {timeout_jobs}")

    # Assertions
    assert completed_jobs == CONCURRENT_JOBS, f"Expected {CONCURRENT_JOBS} completed jobs, got {completed_jobs}"
    assert failed_jobs == 0, f"Expected 0 failed jobs, got {failed_jobs}"
    assert timeout_jobs == 0, f"Expected 0 timeout jobs, got {timeout_jobs}"

    # Verify database consistency
    active_jobs_response = client.get("/api/recruiter/jobs/active")
    assert active_jobs_response.status_code == 200
    active_data = active_jobs_response.json()
    assert active_data["count"] == 0, f"Expected 0 active jobs, got {active_data['count']}"

    print("🎉 Concurrent job execution test PASSED!")


@pytest.mark.asyncio
async def test_job_recovery_mechanism():
    """Test zombie job recovery on startup."""
    import time
    from unittest.mock import patch, AsyncMock

    # Create a job and manually set it to processing (simulating a stuck job)
    client = TestClient(app)

    response = client.post("/api/recruiter/query", json={
        "query": "Test recovery job",
        "recruiter_id": "recovery-test"
    })
    assert response.status_code == 200
    job_data = response.json()
    job_id = job_data["query_id"]

    # Manually update the job to be "old" (simulating it got stuck)
    from app.database import SessionLocal, Query
    from datetime import datetime, timedelta

    db_session = SessionLocal()
    try:
        # Make the job appear 10 minutes old
        old_timestamp = datetime.utcnow() - timedelta(minutes=10)
        job = db_session.query(Query).filter(Query.id == job_id).first()
        if job:
            job.created_at = old_timestamp
            # Ensure it's still in processing state
            job.processing_status = "processing"
            db_session.commit()

        db_session.close()

        # Trigger recovery mechanism
        from app.main import _recover_zombie_jobs
        await _recover_zombie_jobs()

        # Verify job was marked as failed
        db_session = SessionLocal()
        recovered_job = db_session.query(Query).filter(Query.id == job_id).first()
        db_session.close()

        assert recovered_job is not None
        assert recovered_job.processing_status == "failed"
        print("✅ Zombie job recovery test PASSED!")

    except Exception as e:
        if db_session:
            db_session.close()
        raise


@pytest.mark.asyncio
async def test_job_timeout_mechanism():
    """Test that jobs timeout and get marked as failed."""
    import asyncio

    # Create a job that will timeout
    client = TestClient(app)

    # Patch the pipeline to simulate a long-running operation
    with patch('app.services.pipeline.RecruiterPipeline.process_recruiter_query', new_callable=AsyncMock) as mock_pipeline:
        # Make the pipeline take longer than the timeout
        async def slow_pipeline(*args, **kwargs):
            await asyncio.sleep(10)  # Sleep longer than timeout
            return {"status": "completed"}

        mock_pipeline.side_effect = slow_pipeline

        # Submit job
        response = client.post("/api/recruiter/query", json={
            "query": "Test timeout job",
            "recruiter_id": "timeout-test"
        })
        assert response.status_code == 200
        job_data = response.json()
        job_id = job_data["query_id"]

        # Wait for timeout (should be < 5 seconds due to our timeout setting)
        await asyncio.sleep(6)

        # Check job status - should be failed due to timeout
        status_response = client.get(f"/api/recruiter/query/{job_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()

        # Job should be marked as failed due to timeout
        assert status_data["status"] == "failed"
        assert "timeout" in status_data.get("error", "").lower()

        print("✅ Job timeout mechanism test PASSED!")


if __name__ == "__main__":
    pytest.main([__file__])
