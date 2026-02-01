"""
Tests for the Recruiter CLI client.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner

from tools.recruiter_cli import app, Config, APIClient


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_config():
    """Temporary config file for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / ".recruiter" / "config.toml"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Create a test config
        config_path.write_text("""
backend_url = "http://localhost:8000"
""")

        # Create config instance with mocked file path
        config = Config()
        config.config_file = config_path
        config._config = config._load_config()
        yield config


class TestConfig:
    """Test configuration management."""

    def test_config_initialization(self, temp_config):
        """Test config initialization."""
        assert temp_config.get("backend_url") == "http://localhost:8000"

    def test_config_set_get(self, temp_config):
        """Test setting and getting config values."""
        temp_config.set("test_key", "test_value")
        assert temp_config.get("test_key") == "test_value"

    def test_config_get_default(self, temp_config):
        """Test getting config with default value."""
        assert temp_config.get("nonexistent", "default") == "default"


class TestAPIClient:
    """Test API client functionality."""

    @patch('tools.recruiter_cli.requests.Session')
    def test_health_check_success(self, mock_session):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "ok",
            "db": "connected",
            "redis": "connected"
        }
        mock_session.return_value.request.return_value = mock_response

        client = APIClient("http://localhost:8000")
        result = client.health_check()

        assert result["status"] == "ok"
        assert result["db"] == "connected"

    @patch('tools.recruiter_cli.requests.Session')
    def test_submit_query_success(self, mock_session):
        """Test successful query submission."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "query_id": "test-123",
            "status": "processing",
            "original_query": "test query"
        }
        mock_session.return_value.request.return_value = mock_response

        client = APIClient("http://localhost:8000")
        result = client.submit_query("test query", "recruiter-1")

        assert result["query_id"] == "test-123"
        assert result["status"] == "processing"

    @patch('tools.recruiter_cli.requests.Session')
    def test_get_query_status_success(self, mock_session):
        """Test successful query status retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "query_id": "test-123",
            "status": "completed",
            "total_leads_found": 5
        }
        mock_session.return_value.request.return_value = mock_response

        client = APIClient("http://localhost:8000")
        result = client.get_query_status("test-123")

        assert result["status"] == "completed"
        assert result["total_leads_found"] == 5


class TestCLICommands:
    """Test CLI commands."""

    @patch('tools.recruiter_cli.APIClient')
    def test_health_command_success(self, mock_client_class, runner):
        """Test health command with successful response."""
        mock_client = Mock()
        mock_client.health_check.return_value = {
            "status": "ok",
            "db": "connected",
            "redis": "connected",
            "timestamp": "2024-01-01T00:00:00"
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["health"])

        assert result.exit_code == 0
        assert "Backend Status: ok" in result.output
        assert "Database" in result.output
        assert "Redis Cache" in result.output

    @patch('tools.recruiter_cli.APIClient')
    def test_health_command_failure(self, mock_client_class, runner):
        """Test health command with API failure."""
        mock_client_class.return_value.health_check.side_effect = Exception("Connection failed")

        result = runner.invoke(app, ["health"])

        assert result.exit_code == 1
        assert "Error checking health" in result.output

    @patch('tools.recruiter_cli.APIClient')
    def test_query_command_success(self, mock_client_class, runner):
        """Test query command with successful submission."""
        mock_client = Mock()
        mock_client.submit_query.return_value = {
            "query_id": "test-123",
            "status": "processing",
            "original_query": "Find Python developers"
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["query", "Find Python developers", "--recruiter", "1"])

        assert result.exit_code == 0
        assert "Query submitted successfully" in result.output
        assert "test-123" in result.output

    @patch('tools.recruiter_cli.APIClient')
    def test_query_command_with_wait(self, mock_client_class, runner):
        """Test query command with wait option."""
        mock_client = Mock()
        # First call returns processing, second returns completed
        mock_client.submit_query.return_value = {
            "query_id": "test-123",
            "status": "processing",
            "original_query": "Find Python developers"
        }
        mock_client.get_query_status.side_effect = [
            {"query_id": "test-123", "status": "processing"},
            {"query_id": "test-123", "status": "completed", "total_leads_found": 3, "leads": []}
        ]
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["query", "Find Python developers", "--wait"])

        assert result.exit_code == 0
        assert "Query completed" in result.output

    @patch('tools.recruiter_cli.APIClient')
    def test_status_command_success(self, mock_client_class, runner):
        """Test status command."""
        mock_client = Mock()
        mock_client.get_query_status.return_value = {
            "query_id": "test-123",
            "status": "completed",
            "total_leads_found": 5
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["status", "test-123"])

        assert result.exit_code == 0
        assert "Query ID: test-123" in result.output
        assert "Status: completed" in result.output
        assert "Total leads found: 5" in result.output

    @patch('tools.recruiter_cli.APIClient')
    def test_results_command_success(self, mock_client_class, runner):
        """Test results command."""
        mock_client = Mock()
        mock_client.get_query_status.return_value = {
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
                }
            ]
        }
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["results", "test-123"])

        assert result.exit_code == 0
        assert "Find Python developers" in result.output  # Check query text
        assert "completed" in result.output  # Check status
        assert "TechCorp" in result.output
        assert "0.85" in result.output

    @patch('tools.recruiter_cli.APIClient')
    def test_results_command_json_output(self, mock_client_class, runner):
        """Test results command with JSON output."""
        mock_client = Mock()
        expected_result = {
            "query_id": "test-123",
            "status": "completed",
            "total_leads_found": 1
        }
        mock_client.get_query_status.return_value = expected_result
        mock_client_class.return_value = mock_client

        result = runner.invoke(app, ["results", "test-123", "--json"])

        assert result.exit_code == 0
        # Should contain JSON output
        assert "test-123" in result.output

    def test_config_command_get(self, runner, temp_config):
        """Test config get command."""
        with patch('tools.recruiter_cli.cli_config', temp_config):
            result = runner.invoke(app, ["config-cmd", "backend_url"])

            assert result.exit_code == 0
            assert "http://localhost:8000" in result.output

    def test_config_command_set(self, runner, temp_config):
        """Test config set command."""
        with patch('tools.recruiter_cli.cli_config', temp_config):
            result = runner.invoke(app, ["config-cmd", "backend_url", "http://new-url:9000"])

            assert result.exit_code == 0
            assert "backend_url = http://new-url:9000" in result.output

            # Verify it was actually set
            assert temp_config.get("backend_url") == "http://new-url:9000"


if __name__ == "__main__":
    pytest.main([__file__])
