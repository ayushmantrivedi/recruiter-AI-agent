
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
            
            # CRITICAL: If using sqlite :memory:, we must use StaticPool to share state
            from sqlalchemy.pool import StaticPool
            from sqlalchemy import create_engine
            from app import database
            
            test_engine = create_engine(
                "sqlite:///:memory:",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
            
            with patch("app.database.engine", test_engine), \
                 patch("app.database.SessionLocal", database.sessionmaker(autocommit=False, autoflush=False, bind=test_engine)):
                yield

@pytest.fixture(autouse=True)
def setup_database(mock_settings_env):
    """Initialize the in-memory database with tables."""
    from app.database import engine, Base
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def mock_session_local():
    """Global patch to prevent real DB access in pipeline while allowing it in routes if needed."""
    # Only patch if we really want to mock it. 
    # For now, let's keep it but ensure it's not breaking everything.
    with patch("app.services.pipeline.SessionLocal") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock
