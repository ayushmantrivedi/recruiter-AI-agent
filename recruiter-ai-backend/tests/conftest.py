
import pytest
import os
import sys
from unittest.mock import MagicMock, patch

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(autouse=True)
def mock_settings_env():
    """Force safe execution mode for all tests."""
    with patch.dict(os.environ, {
        "SEARCH_MODE": "dev",
        "ENABLE_PAID_APIS": "false",
        "ENABLE_MOCK_SOURCES": "true",
        "LOG_LEVEL": "DEBUG",
        "DATABASE_URL": "sqlite:///:memory:",
        "REDIS_URL": "redis://mock-redis:6379/0"
    }):
        # We also need to patch the Settings object if it's already instantiated
        with patch("app.config.settings.agent.search_mode", "dev"), \
             patch("app.config.settings.agent.enable_paid_apis", False), \
             patch("app.config.settings.agent.enable_mock_sources", True):
            yield

@pytest.fixture(autouse=True)
def mock_session_local():
    """Global patch to prevent real DB access."""
    with patch("app.services.pipeline.SessionLocal") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock
