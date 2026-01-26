from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    name: str = Field(default="recruiter_ai", env="DB_NAME")
    user: str = Field(default="recruiter_user", env="DB_USER")
    password: SecretStr = Field(default=SecretStr("recruiter_pass"), env="DB_PASSWORD")

    @property
    def url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[SecretStr] = Field(default=None, env="REDIS_PASSWORD")

    @property
    def url(self) -> str:
        if self.redis_url:
            return self.redis_url
        auth = f":{self.password.get_secret_value()}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class APISettings(BaseSettings):
    """API configuration settings."""
    openai_api_key: Optional[SecretStr] = Field(default=None, env="OPENAI_API_KEY")
    huggingface_token: Optional[SecretStr] = Field(default=None, env="HUGGINGFACE_TOKEN")

    # Free API rate limits
    arbeitnow_rate_limit: int = Field(default=100, env="ARBEITNOW_RATE_LIMIT")
    github_jobs_rate_limit: int = Field(default=50, env="GITHUB_JOBS_RATE_LIMIT")
    mediastack_rate_limit: int = Field(default=500, env="MEDIASTACK_RATE_LIMIT")


from enum import Enum

class SearchMode(str, Enum):
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"

class AgentSettings(BaseSettings):
    """Agent configuration settings."""
    # Search Mode (Controls provider enablement)
    search_mode: SearchMode = Field(default=SearchMode.DEV, env="SEARCH_MODE")
    
    # Provider Flags - Controlled by SearchMode
    enable_mock_sources: bool = Field(default=True, env="ENABLE_MOCK_SOURCES")
    enable_arbeitnow: bool = Field(default=True, env="ENABLE_ARBEITNOW") 
    enable_github_jobs: bool = Field(default=False, env="ENABLE_GITHUB_JOBS") # DEPRECATED
    enable_paid_apis: bool = Field(default=False, env="ENABLE_PAID_APIS")

    # Circuit Breaker Config
    external_api_timeout: float = Field(default=5.0, env="EXTERNAL_API_TIMEOUT")
    external_api_circuit_breaker_threshold: int = Field(default=3, env="EXTERNAL_API_CIRCUIT_BREAKER_THRESHOLD")

    # Concept Reasoner
    concept_model_name: str = Field(default="bert-base-uncased", env="CONCEPT_MODEL_NAME")
    reasoning_model: str = Field(default="gpt-3.5-turbo", env="REASONING_MODEL")

    # Action Orchestrator
    max_steps: int = Field(default=10, env="MAX_STEPS")
    confidence_threshold: float = Field(default=0.85, env="CONFIDENCE_THRESHOLD")
    marginal_value_epsilon: float = Field(default=0.01, env="MARGINAL_VALUE_EPSILON")

    # Tool priorities and costs
    tool_costs: dict = Field(default_factory=lambda: {
        "arbeitnow": 0.0,
        "github_jobs": 0.0,
        "mediastack": 0.0,
        "company_metadata": 0.1
    })

    tool_latencies: dict = Field(default_factory=lambda: {
        "arbeitnow": 1.0,
        "github_jobs": 1.5,
        "mediastack": 2.0,
        "company_metadata": 3.0
    })
    
    @model_validator(mode='after')
    def enforce_search_mode_rules(self):
        """Enforce provider flags based on Search Mode.
        CRITICAL: This ensures we never accidentally mock in prod or pay in dev.
        """
        if self.search_mode == SearchMode.DEV:
            self.enable_mock_sources = True
            # In DEV, we can toggle external APIs manually if needed, but default safe
            if self.enable_paid_apis:
                 raise ValueError("Cannot enable PAID APIs in DEV mode. Switch to STAGING or PRODUCTION.")
            
        elif self.search_mode == SearchMode.STAGING:
            # Staging: Public APIs allowed, Mocks disabled
            self.enable_mock_sources = False
            self.enable_paid_apis = False # Safe default
            
        elif self.search_mode == SearchMode.PRODUCTION:
            # Production: Paid APIs only, NO mocks
            if self.enable_mock_sources:
                raise ValueError("Cannot enable MOCK sources in PRODUCTION mode.")
            self.enable_arbeitnow = False 
            self.enable_github_jobs = False
            self.enable_paid_apis = True
            
        return self


class ExecutionMode(str, Enum):
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"

class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    # Profiles
    mode: ExecutionMode = Field(default=ExecutionMode.DEV, env="EXECUTION_MODE")
    
    # Common
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="json", env="LOG_FORMAT")
    
    # File Paths (For DEV/STAGING)
    app_log_path: str = "logs/app.log"
    pipeline_log_path: str = "logs/pipeline.log"
    search_log_path: str = "logs/search.log"
    
    sentry_dsn: Optional[SecretStr] = Field(default=None, env="SENTRY_DSN")


class Settings(BaseSettings):
    """Main application settings."""
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # Application
    app_name: str = "Recruiter AI Platform"
    app_version: str = "1.0.0"
    secret_key: SecretStr = Field(default=SecretStr(os.urandom(32).hex()), env="SECRET_KEY")

    # API
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")

    # Billing
    billing_enabled: bool = Field(default=False, env="BILLING_ENABLED")
    stripe_secret_key: Optional[SecretStr] = Field(default=None, env="STRIPE_SECRET_KEY")

    # Sub-settings
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    api: APISettings = APISettings()
    agent: AgentSettings = AgentSettings()
    logging: LoggingSettings = LoggingSettings()

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global settings instance
settings = Settings()
