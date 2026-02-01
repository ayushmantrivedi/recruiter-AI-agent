
import structlog
import logging
import sys
from typing import Any, Dict

# Define these first to avoid ImportError in circular scenarios
def log_agent_action(agent_name: str, action: str, **kwargs):
    get_logger("recruiter_ai").info("agent_action", agent=agent_name, action=action, **kwargs)

def log_lead_generation(query_id: str, company: str, score: float, reasons: list, **kwargs):
    get_logger("recruiter_ai").info("lead_generated", query_id=query_id, company=company, score=score, reasons=reasons, **kwargs)

def log_pipeline_decision(query_id: str, component: str, decision: str, reason: str, **kwargs):
    get_logger("recruiter_ai").info("pipeline_decision", query_id=query_id, component=component, decision=decision, reason=reason, **kwargs)

def log_api_call(api_name: str, endpoint: str, success: bool, latency: float, **kwargs):
    get_logger("recruiter_ai").info("api_call", api=api_name, endpoint=endpoint, success=success, latency=latency, **kwargs)

def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)

# Configure later
def setup_logging():
    from ..config import settings, ExecutionMode
    
    if settings.logging.mode == ExecutionMode.DEV:
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.logging.level.upper())
        ),
        cache_logger_on_first_use=True,
    )
    
    # Stdlib redirection
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.logging.level.upper()),
    )
    
    # Silence uvicorn
    logging.getLogger("uvicorn.access").handlers = []

# Global logger initialization
logger = get_logger("recruiter_ai")
