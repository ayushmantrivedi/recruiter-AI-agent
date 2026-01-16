import structlog
import logging
from typing import Any, Dict
from ..config import settings


def setup_logging():
    """Configure structured logging for the application."""
    # Create logs directory if it doesn't exist
    import os
    from ..config import ExecutionMode
    
    handlers = [logging.StreamHandler()]
    
    # In DEV/STAGING, add file handlers
    if settings.logging.mode in [ExecutionMode.DEV, ExecutionMode.STAGING]:
        os.makedirs("logs", exist_ok=True)
        
        # App Log
        file_handler = logging.FileHandler(settings.logging.app_log_path)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        handlers.append(file_handler)
        
        # Pipeline Log
        pipeline_handler = logging.FileHandler(settings.logging.pipeline_log_path)
        pipeline_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        pipeline_logger = logging.getLogger("pipeline")
        pipeline_logger.addHandler(pipeline_handler)
        pipeline_logger.propagate = True # Also go to main log
        
        # Search Log
        search_handler = logging.FileHandler(settings.logging.search_log_path)
        search_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        search_logger = logging.getLogger("search_orchestrator")
        search_logger.addHandler(search_handler)
        search_logger.propagate = True
        
    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, settings.logging.level.upper()),
        format="%(message)s",
        handlers=handlers,
        force=True # Override existing config
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
        logger_factory=structlog.WriteLoggerFactory(
            file=open(settings.logging.app_log_path, "a") if settings.logging.mode in [ExecutionMode.DEV, ExecutionMode.STAGING] else None
        ),
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
