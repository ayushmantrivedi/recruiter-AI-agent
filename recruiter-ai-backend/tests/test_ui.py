"""
Tests for the HTML UI routes.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from app.main import app


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


class TestUIRoutes:
    """Test UI route functionality."""

    def test_ui_home_page(self, client):
        """Test home page loads successfully."""
        response = client.get("/ui")

        assert response.status_code == 200
        assert "Recruiter AI" in response.text
        assert "Submit a Recruiter Query" in response.text
        assert "htmx" in response.text.lower()  # Check HTMX is included

    @patch('app.routes.recruiter.process_recruiter_query')
    def test_ui_query_submission_success(self, mock_process_query, client):
        """Test successful query submission via UI."""
        # Mock the process_recruiter_query function
        mock_process_query.return_value = {
            "query_id": "test-123",
            "status": "processing",
            "original_query": "Find Python developers"
        }

        response = client.post("/ui/query", data={
            "query": "Find Python developers",
            "recruiter_id": "1"
        })

        assert response.status_code == 200
        assert "Processing Your Query" in response.text
        assert "test-123" in response.text

    @patch('app.routes.recruiter.process_recruiter_query')
    def test_ui_query_submission_completed(self, mock_process_query, client):
        """Test UI query display when completed."""
        # Mock the process_recruiter_query function
        mock_process_query.return_value = {
            "query_id": "test-123",
            "status": "completed",
            "original_query": "Find Python developers",
            "total_leads_found": 2,
            "processing_time": 5.5,
            "leads": [
                {
                    "company": "TechCorp",
                    "score": 0.85,
                    "confidence": 0.9,
                    "evidence_count": 5,
                    "reasons": ["Strong match", "Recent hiring"]
                },
                {
                    "company": "DevInc",
                    "score": 0.75,
                    "confidence": 0.8,
                    "evidence_count": 3,
                    "reasons": ["Good fit"]
                }
            ]
        }

        response = client.post("/ui/query", data={
            "query": "Find Python developers"
        })

        assert response.status_code == 200
        assert "Query Completed" in response.text
        assert "TechCorp" in response.text
        assert "DevInc" in response.text
        assert "2 leads found" in response.text

    @patch('app.routes.recruiter.process_recruiter_query')
    def test_ui_query_submission_failed(self, mock_process_query, client):
        """Test UI query display when failed."""
        # Mock the process_recruiter_query function to raise an exception
        mock_process_query.side_effect = Exception("API Error")

        response = client.post("/ui/query", data={
            "query": "Find Python developers"
        })

        assert response.status_code == 200
        assert "Query Failed" in response.text
        assert "API Error" in response.text

    @patch('app.routes.recruiter.get_query_results')
    def test_ui_query_status_polling(self, mock_get_results, client):
        """Test query status polling via UI."""
        # Mock the get_query_results function
        mock_get_results.return_value = {
            "query_id": "test-123",
            "status": "completed",
            "original_query": "Find Python developers",
            "total_leads_found": 1,
            "leads": []
        }

        response = client.get("/ui/query/test-123")

        assert response.status_code == 200
        assert "Query Completed" in response.text
        assert "test-123" in response.text

    @patch('app.routes.recruiter.get_query_results')
    def test_ui_query_status_polling_failed(self, mock_get_results, client):
        """Test query status polling when API fails."""
        # Mock the get_query_results function to raise an exception
        mock_get_results.side_effect = Exception("Connection failed")

        response = client.get("/ui/query/test-123")

        assert response.status_code == 200
        assert "Query Failed" in response.text
        assert "Connection failed" in response.text


class TestUITemplates:
    """Test UI template rendering."""

    def test_home_template_structure(self, client):
        """Test home page has correct HTML structure."""
        response = client.get("/ui")

        # Check for required HTML elements
        assert "<!DOCTYPE html>" in response.text
        assert "<form" in response.text
        assert 'hx-post="/ui/query"' in response.text
        assert 'name="query"' in response.text
        assert 'name="recruiter_id"' in response.text

        # Check for Tailwind classes
        assert "tailwindcss" in response.text

        # Check for HTMX attributes
        assert "hx-indicator" in response.text

    def test_query_result_template_processing(self, client):
        """Test processing state template."""
        with patch('app.routes.recruiter.process_recruiter_query') as mock_process_query:
            mock_process_query.return_value = {
                "query_id": "test-123",
                "status": "processing",
                "original_query": "Test query"
            }

            response = client.post("/ui/query", data={"query": "Test query"})

            assert "Processing Your Query" in response.text
            assert "Test query" in response.text
            assert "test-123" in response.text
            assert "animate-spin" in response.text  # Loading spinner

    def test_query_result_template_completed(self, client):
        """Test completed state template."""
        with patch('app.routes.recruiter.process_recruiter_query') as mock_process_query:
            mock_process_query.return_value = {
                "query_id": "test-123",
                "status": "completed",
                "original_query": "Test query",
                "total_leads_found": 1,
                "processing_time": 2.5,
                "leads": [
                    {
                        "company": "TestCompany",
                        "score": 0.9,
                        "confidence": 0.85,
                        "evidence_count": 4,
                        "reasons": ["Good match", "Recent activity"]
                    }
                ]
            }

            response = client.post("/ui/query", data={"query": "Test query"})

            assert "Query Completed" in response.text
            assert "TestCompany" in response.text
            assert "0.9" in response.text  # Score
            assert "2.5" in response.text  # Processing time
            assert "Good match" in response.text

    def test_query_result_template_failed(self, client):
        """Test failed state template."""
        with patch('app.routes.recruiter.process_recruiter_query') as mock_process_query:
            mock_process_query.return_value = {
                "query_id": "test-123",
                "status": "failed",
                "original_query": "Test query",
                "error": "Test error message"
            }

            response = client.post("/ui/query", data={"query": "Test query"})

            assert "Query Failed" in response.text
            assert "Test error message" in response.text
            assert "test-123" in response.text


class TestUIStaticFiles:
    """Test static file serving."""

    def test_static_files_mounted(self, client):
        """Test that static files are properly mounted."""
        # This would test if static files are served, but since we don't have any,
        # we'll just verify the mount point exists by checking the app structure
        assert "/static" in str(app.routes)  # Check if static route is mounted


if __name__ == "__main__":
    pytest.main([__file__])
