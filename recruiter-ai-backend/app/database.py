from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func, text
from .config import settings
from .utils.logger import get_logger
import time

logger = get_logger("database")

# Create database engine
engine = create_engine(
    settings.database.url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


class Recruiter(Base):
    """Recruiter user model."""
    __tablename__ = "recruiters"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    company = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # Note: relationships removed to avoid foreign key issues since recruiter_id is used as string identifier


class RecruiterPreferences(Base):
    """Recruiter preference settings."""
    __tablename__ = "recruiter_preferences"

    id = Column(Integer, primary_key=True)
    recruiter_id = Column(Integer, ForeignKey("recruiters.id"), nullable=False)

    # Search preferences
    default_region = Column(String(100), default="remote")
    default_role_types = Column(JSON, default=list)  # List of role categories
    excluded_companies = Column(JSON, default=list)
    preferred_industries = Column(JSON, default=list)

    # Agent preferences
    max_budget_per_search = Column(Float, default=1.0)
    confidence_threshold = Column(Float, default=0.8)
    max_results = Column(Integer, default=20)

    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    weekly_digest = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    # Note: recruiter relationship removed to avoid foreign key issues


class Query(Base):
    """Recruiter search query model."""
    __tablename__ = "queries"

    id = Column(String(36), primary_key=True, index=True)
    recruiter_id = Column(String(255), nullable=True)  # Changed to string to match API contract
    query_text = Column(Text, nullable=False)

    # Agent processing results
    concept_vector = Column(JSON, nullable=True)  # Legacy support
    intelligence = Column(JSON, nullable=True)    # New structured metadata
    signals = Column(JSON, nullable=True)         # New numeric metrics
    constraints = Column(JSON)     # Derived constraints
    confidence_score = Column(Float)
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed

    # Metadata
    total_cost = Column(Float, default=0.0)
    execution_time = Column(Float)  # seconds
    tools_used = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    # Note: recruiter relationship removed since recruiter_id is used as string identifier, not foreign key
    leads = relationship("Lead", back_populates="query")
    executions = relationship("AgentExecution", back_populates="query")


class Lead(Base):
    """Generated hiring lead model."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(String(36), ForeignKey("queries.id"), nullable=False)

    # Company information
    company_name = Column(String(255), nullable=False)
    company_domain = Column(String(255))
    company_size = Column(String(50))
    industry = Column(String(100))

    # Lead scoring
    score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    reasons = Column(JSON, default=list)  # List of evidence-based reasons

    # Contact information (if available)
    linkedin_url = Column(String(500))
    website_url = Column(String(500))
    hiring_manager = Column(String(255))

    # Evidence data
    evidence_objects = Column(JSON, default=list)  # Raw evidence from APIs
    job_postings = Column(JSON, default=list)     # Related job data
    news_mentions = Column(JSON, default=list)    # Recent news

    # Status
    status = Column(String(50), default="new")  # new, contacted, interested, hired
    outreach_generated = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    query = relationship("Query", back_populates="leads")


class AgentExecution(Base):
    """Agent execution step tracking."""
    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(String(36), ForeignKey("queries.id"), nullable=False)

    # Execution details
    step_number = Column(Integer, nullable=False)
    tool_name = Column(String(100), nullable=False)
    tool_params = Column(JSON)
    execution_start = Column(DateTime(timezone=True), server_default=func.now())
    execution_end = Column(DateTime(timezone=True))
    execution_time = Column(Float)

    # Results
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    api_response = Column(JSON)  # Raw API response
    signal_quality = Column(Float)  # 0.0 to 1.0
    cost_incurred = Column(Float, default=0.0)

    # Agent state
    confidence_before = Column(Float)
    confidence_after = Column(Float)
    marginal_value = Column(Float)

    # Relationships
    query = relationship("Query", back_populates="executions")


class APIFeedback(Base):
    """API performance feedback for learning."""
    __tablename__ = "api_feedback"

    id = Column(Integer, primary_key=True, index=True)
    tool_name = Column(String(100), nullable=False)
    intent_signature = Column(String(500), nullable=False)  # Hash of concept vector

    # Performance metrics
    success_rate = Column(Float, default=1.0)
    avg_latency = Column(Float, nullable=False)
    avg_cost = Column(Float, default=0.0)
    avg_signal_quality = Column(Float, nullable=False)

    # Usage statistics
    total_calls = Column(Integer, default=1)
    successful_calls = Column(Integer, default=1)
    failed_calls = Column(Integer, default=0)

    # Learning data
    best_for_concepts = Column(JSON, default=list)  # Concept vectors this tool excels at
    noise_level = Column(Float, default=0.0)       # Amount of irrelevant data returned

    # Metadata
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_api_feedback_tool_intent', 'tool_name', 'intent_signature'),
        Index('idx_api_feedback_performance', 'success_rate', 'avg_signal_quality'),
    )


class BillingRecord(Base):
    """Billing and usage tracking."""
    __tablename__ = "billing_records"

    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("recruiters.id"), nullable=False)

    # Billing details
    billing_type = Column(String(50), nullable=False)  # per_run, per_lead, per_seat
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")

    # Related entities
    query_id = Column(String(36), ForeignKey("queries.id"))
    lead_id = Column(Integer, ForeignKey("leads.id"))

    # Stripe/payment details
    stripe_payment_id = Column(String(255))
    status = Column(String(50), default="pending")  # pending, paid, failed, refunded

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    recruiter = relationship("Recruiter")


def test_db_connection(max_retries: int = 3, retry_delay: float = 2.0) -> bool:
    """Test database connection with retry logic."""
    for attempt in range(max_retries):
        try:
            logger.info("Testing database connection",
                       attempt=attempt + 1,
                       max_retries=max_retries,
                       database_url=settings.database.url.replace(settings.database.password.get_secret_value() if settings.database.password else "", "***"))

            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()

            logger.info("Database connection successful")
            return True

        except Exception as e:
            logger.warning("Database connection attempt failed",
                         attempt=attempt + 1,
                         error=str(e))
            if attempt < max_retries - 1:
                logger.info("Retrying database connection",
                          attempt=attempt + 1,
                          retry_delay=retry_delay)
                time.sleep(retry_delay)
            else:
                logger.error("Database connection failed after all retries",
                           max_retries=max_retries,
                           error=str(e))
                return False


def create_tables():
    """Create all database tables with connection validation."""
    logger.info("Creating database tables")

    # First test connection
    if not test_db_connection():
        raise Exception("Cannot create tables: database connection failed")

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise


# Database dependency
def get_db():
    """Database session dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
