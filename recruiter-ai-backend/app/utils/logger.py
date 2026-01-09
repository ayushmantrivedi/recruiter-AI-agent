import structlog
import logging
from typing import Any, Dict
from ..config import settings


def setup_logging():
    """Configure structured logging for the application."""
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, settings.logging.level.upper()),
        format="%(message)s",
        handlers=[logging.StreamHandler()]
    )

    # Configure structlog
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
        if settings.logging.format == "json"
        else structlog.processors.KeyValueRenderer()
    ]

    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.logging.level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Global logger instance
logger = get_logger("recruiter_ai")


def log_agent_action(
    agent_name: str,
    action: str,
    query_id: str = None,
    tool_name: str = None,
    **kwargs
):
    """Log agent actions with structured data."""
    log_data = {
        "agent": agent_name,
        "action": action,
        "query_id": query_id,
        "tool_name": tool_name,
        **kwargs
    }
    logger.info("agent_action", **log_data)


def log_api_call(
    tool_name: str,
    endpoint: str,
    latency: float,
    cost: float = 0.0,
    success: bool = True,
    **kwargs
):
    """Log API calls with performance metrics."""
    log_data = {
        "tool": tool_name,
        "endpoint": endpoint,
        "latency": latency,
        "cost": cost,
        "success": success,
        **kwargs
    }
    logger.info("api_call", **log_data)


def log_concept_inference(
    query_id: str,
    concept_vector: Dict[str, float],
    constraints: Dict[str, Any],
    confidence: float = None
):
    """Log concept reasoning results."""
    logger.info(
        "concept_inference",
        query_id=query_id,
        concept_vector=concept_vector,
        constraints=constraints,
        confidence=confidence
    )


def log_lead_generation(
    query_id: str,
    company: str,
    score: float,
    reasons: list,
    evidence_count: int
):
    """Log lead generation results."""
    logger.info(
        "lead_generated",
        query_id=query_id,
        company=company,
        score=score,
        reasons=reasons,
        evidence_count=evidence_count
    )


def log_billing_event(
    recruiter_id: str,
    billing_type: str,
    amount: float,
    query_id: str = None,
    lead_id: str = None
):
    """Log billing events."""
    logger.info(
        "billing_event",
        recruiter_id=recruiter_id,
        billing_type=billing_type,
        amount=amount,
        query_id=query_id,
        lead_id=lead_id
    )
