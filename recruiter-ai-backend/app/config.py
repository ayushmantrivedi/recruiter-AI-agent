from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    name: str = Field(default="recruiter_ai", env="DB_NAME")
    user: str = Field(default="recruiter_user", env="DB_USER")
    password: SecretStr = Field(default=SecretStr("recruiter_pass"), env="DB_PASSWORD")

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[SecretStr] = Field(default=None, env="REDIS_PASSWORD")

    @property
    def url(self) -> str:
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


class AgentSettings(BaseSettings):
    """Agent configuration settings."""
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


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="json", env="LOG_FORMAT")
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


# Global settings instance
settings = Settings()
