import asyncio
import json
import hashlib
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from ..config import settings
from ..utils.logger import get_logger, log_agent_action
from ..utils.cache import cache
from ..apis.job_apis import job_api_manager
from ..apis.news_apis import news_api_manager
from ..database import SessionLocal, APIFeedback
from sqlalchemy.orm import Session


logger = get_logger("action_orchestrator")


@dataclass
class Tool:
    """Represents a tool in the registry."""
    name: str
    function: Callable
    cost: float
    latency: float
    signal_type: str  # 'job_postings', 'company_news', 'company_metadata'
    best_for_concepts: Dict[str, float]  # Concept vector weights
    description: str


@dataclass
class ToolResult:
    """Result from tool execution."""
    tool_name: str
    success: bool
    data: Any
    latency: float
    cost: float
    signal_quality: float
    error_message: Optional[str] = None


class ActionOrchestrator:
    """Action Orchestrator agent implementing LAM behavior.

    Core brain that:
    - Maintains tool registry
    - Implements action policy
    - Runs execution loop
    - Learns from feedback
    """

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.feedback_memory: Dict[str, Dict[str, Any]] = {}
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize the tool registry with available APIs."""
        self.tools = {
            "arbeitnow_jobs": Tool(
                name="arbeitnow_jobs",
                function=self._execute_arbeitnow_search,
                cost=settings.agent.tool_costs.get("arbeitnow", 0.0),
                latency=settings.agent.tool_latencies.get("arbeitnow", 1.0),
                signal_type="job_postings",
                best_for_concepts={
                    "hiring_pressure": 0.8,
                    "role_scarcity": 0.6,
                    "outsourcing_likelihood": 0.4
                },
                description="Search recent job postings on Arbeitnow"
            ),
            "github_jobs": Tool(
                name="github_jobs",
                function=self._execute_github_search,
                cost=settings.agent.tool_costs.get("github_jobs", 0.0),
                latency=settings.agent.tool_latencies.get("github_jobs", 1.5),
                signal_type="job_postings",
                best_for_concepts={
                    "hiring_pressure": 0.6,
                    "role_scarcity": 0.8,
                    "outsourcing_likelihood": 0.3
                },
                description="Search developer job postings on GitHub"
            ),
            "company_news": Tool(
                name="company_news",
                function=self._execute_news_search,
                cost=settings.agent.tool_costs.get("mediastack", 0.0),
                latency=settings.agent.tool_latencies.get("mediastack", 2.0),
                signal_type="company_news",
                best_for_concepts={
                    "hiring_pressure": 0.7,
                    "role_scarcity": 0.5,
                    "outsourcing_likelihood": 0.6
                },
                description="Fetch recent news and growth signals for companies"
            ),
            "company_metadata": Tool(
                name="company_metadata",
                function=self._execute_metadata_search,
                cost=settings.agent.tool_costs.get("company_metadata", 0.1),
                latency=settings.agent.tool_latencies.get("company_metadata", 3.0),
                signal_type="company_metadata",
                best_for_concepts={
                    "hiring_pressure": 0.4,
                    "role_scarcity": 0.7,
                    "outsourcing_likelihood": 0.8
                },
                description="Fetch detailed company information and hiring patterns"
            )
        }

    async def orchestrate_search(self, query_id: str, concept_vector: Dict[str, float],
                               constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Main orchestration loop implementing the LAM execution policy.

        Args:
            query_id: Unique query identifier
            concept_vector: Concept scores from Concept Reasoner
            constraints: Structured constraints from Concept Reasoner

        Returns:
            Orchestration results with evidence objects
        """
        try:
            logger.info("Starting action orchestration", query_id=query_id)

            # Initialize orchestration state
            state = {
                "query_id": query_id,
                "confidence": 0.0,
                "steps_completed": 0,
                "total_cost": 0.0,
                "evidence_objects": [],
                "execution_history": []
            }

            # Load previous state if resuming
            cached_state = await cache.get_agent_state(query_id, "action_orchestrator")
            if cached_state:
                state.update(cached_state)
                logger.info("Resumed from cached state", steps_completed=state["steps_completed"])

            # Main execution loop
            max_steps = settings.agent.max_steps
            confidence_threshold = settings.agent.confidence_threshold
            marginal_epsilon = settings.agent.marginal_value_epsilon

            while (state["confidence"] < confidence_threshold and
                   state["steps_completed"] < max_steps):

                # Select best tool for current state
                tool_name, tool_score = await self._select_best_tool(concept_vector, state)

                if not tool_name:
                    logger.info("No suitable tools available, ending orchestration")
                    break

                # Execute tool
                result = await self._execute_tool(tool_name, constraints, state)

                # Update state with results
                state["execution_history"].append({
                    "step": state["steps_completed"] + 1,
                    "tool": tool_name,
                    "tool_score": tool_score,
                    "success": result.success,
                    "latency": result.latency,
                    "cost": result.cost,
                    "signal_quality": result.signal_quality
                })

                if result.success and result.data:
                    state["evidence_objects"].extend(result.data)

                state["total_cost"] += result.cost
                state["steps_completed"] += 1

                # Update confidence based on signal quality
                new_confidence = self._calculate_confidence(state)
                marginal_value = new_confidence - state["confidence"]
                state["confidence"] = new_confidence

                # Log step completion
                log_agent_action(
                    agent_name="action_orchestrator",
                    action="tool_execution",
                    query_id=query_id,
                    tool_name=tool_name,
                    confidence=state["confidence"],
                    marginal_value=marginal_value
                )

                # Check exit conditions
                if marginal_value < marginal_epsilon:
                    logger.info("Marginal value below threshold, ending orchestration",
                              marginal_value=marginal_value, epsilon=marginal_epsilon)
                    break

                # Save state for resumability
                await cache.save_agent_state(query_id, "action_orchestrator", state)

                # Brief pause between steps
                await asyncio.sleep(0.1)

            # Finalize results
            result = {
                "query_id": query_id,
                "confidence": state["confidence"],
                "total_steps": state["steps_completed"],
                "total_cost": state["total_cost"],
                "evidence_objects": state["evidence_objects"],
                "execution_summary": state["execution_history"],
                "completed_at": datetime.utcnow().isoformat()
            }

            logger.info("Action orchestration completed",
                       query_id=query_id,
                       confidence=state["confidence"],
                       steps=state["steps_completed"],
                       evidence_count=len(state["evidence_objects"]))

            return result

        except Exception as e:
            logger.error("Action orchestration failed", error=str(e), query_id=query_id)
            raise

    async def _select_best_tool(self, concept_vector: Dict[str, float],
                               state: Dict[str, Any]) -> Tuple[Optional[str], float]:
        """Select the best tool based on concept alignment and learning feedback."""

        try:
            # Create intent signature for feedback lookup
            intent_signature = self._create_intent_signature(concept_vector)

            tool_scores = {}

            for tool_name, tool in self.tools.items():
                # Base score from concept alignment
                concept_score = self._calculate_concept_alignment(tool, concept_vector)

                # Adjust based on learning feedback
                feedback_multiplier = await self._get_feedback_multiplier(tool_name, intent_signature)

                # Penalize recently used tools to encourage diversity
                recency_penalty = self._calculate_recency_penalty(tool_name, state)

                # Final score
                final_score = concept_score * feedback_multiplier * recency_penalty
                tool_scores[tool_name] = final_score

            # Select highest scoring tool
            if tool_scores:
                best_tool = max(tool_scores.items(), key=lambda x: x[1])
                logger.debug("Tool selection completed",
                           best_tool=best_tool[0],
                           score=best_tool[1],
                           all_scores=tool_scores)
                return best_tool

            return None, 0.0

        except Exception as e:
            logger.error("Tool selection failed", error=str(e))
            return None, 0.0

    def _calculate_concept_alignment(self, tool: Tool, concept_vector: Dict[str, float]) -> float:
        """Calculate how well a tool aligns with the current concept vector."""
        try:
            alignment = 0.0
            total_weight = 0.0

            for concept, weight in tool.best_for_concepts.items():
                if concept in concept_vector:
                    alignment += concept_vector[concept] * weight
                    total_weight += weight

            return alignment / total_weight if total_weight > 0 else 0.0

        except Exception as e:
            logger.error("Concept alignment calculation failed", error=str(e))
            return 0.0

    async def _get_feedback_multiplier(self, tool_name: str, intent_signature: str) -> float:
        """Get learning-based multiplier from feedback memory."""
        try:
            # Check cache first
            cache_key = f"feedback:{tool_name}:{intent_signature}"
            cached_multiplier = await cache.get(cache_key)

            if cached_multiplier is not None:
                return float(cached_multiplier)

            # Query database for feedback
            db = SessionLocal()
            try:
                feedback = db.query(APIFeedback).filter(
                    APIFeedback.tool_name == tool_name,
                    APIFeedback.intent_signature == intent_signature
                ).first()

                if feedback and feedback.total_calls > 0:
                    # Calculate multiplier based on success rate and signal quality
                    base_multiplier = feedback.success_rate * feedback.avg_signal_quality

                    # Boost for high performance, penalize for low performance
                    if base_multiplier > 0.8:
                        multiplier = 1.2  # Boost good tools
                    elif base_multiplier < 0.3:
                        multiplier = 0.5  # Penalize bad tools
                    else:
                        multiplier = 1.0  # Neutral
                else:
                    multiplier = 1.0  # No feedback, neutral

                # Cache for 1 hour
                await cache.set(cache_key, multiplier, ttl=3600)
                return multiplier

            finally:
                db.close()

        except Exception as e:
            logger.error("Feedback lookup failed", error=str(e))
            return 1.0

    def _calculate_recency_penalty(self, tool_name: str, state: Dict[str, Any]) -> float:
        """Calculate penalty for recently used tools to encourage diversity."""
        try:
            recent_usage = [
                step for step in state.get("execution_history", [])
                if step["tool"] == tool_name
            ]

            if not recent_usage:
                return 1.0  # No penalty if never used

            # Exponential decay penalty based on recent usage
            penalty = 0.9 ** len(recent_usage)  # 10% penalty per recent use
            return max(0.3, penalty)  # Minimum penalty of 0.3

        except Exception as e:
            logger.error("Recency penalty calculation failed", error=str(e))
            return 1.0

    async def _execute_tool(self, tool_name: str, constraints: Dict[str, Any],
                           state: Dict[str, Any]) -> ToolResult:
        """Execute a tool and return standardized result."""
        try:
            tool = self.tools.get(tool_name)
            if not tool:
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    data=None,
                    latency=0.0,
                    cost=0.0,
                    signal_quality=0.0,
                    error_message="Tool not found"
                )

            start_time = asyncio.get_event_loop().time()

            # Execute tool function
            result_data = await tool.function(constraints, state)

            latency = asyncio.get_event_loop().time() - start_time

            # Evaluate signal quality
            signal_quality = self._evaluate_signal_quality(result_data, tool.signal_type)

            # Update feedback memory
            await self._update_feedback_memory(tool_name, result_data, latency, signal_quality)

            return ToolResult(
                tool_name=tool_name,
                success=True,
                data=result_data,
                latency=latency,
                cost=tool.cost,
                signal_quality=signal_quality
            )

        except Exception as e:
            logger.error("Tool execution failed", error=str(e), tool_name=tool_name)
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                latency=0.0,
                cost=0.0,
                signal_quality=0.0,
                error_message=str(e)
            )

    def _evaluate_signal_quality(self, data: Any, signal_type: str) -> float:
        """Evaluate the quality of signal data returned by a tool."""
        try:
            if not data:
                return 0.0

            if signal_type == "job_postings":
                # Quality based on number of relevant jobs and recency
                jobs = data.get("jobs", [])
                if not jobs:
                    return 0.0

                # Base quality on count (more jobs = higher quality, up to a point)
                count_score = min(1.0, len(jobs) / 20.0)  # Max at 20 jobs

                # Boost for recent jobs (would need date parsing in production)
                recency_score = 0.8  # Placeholder

                return (count_score + recency_score) / 2.0

            elif signal_type == "company_news":
                # Quality based on relevance and recency of news
                news = data.get("news", [])
                if not news:
                    return 0.0

                # Average relevance score
                relevance_scores = [article.get("relevance_score", 0.0) for article in news]
                avg_relevance = np.mean(relevance_scores) if relevance_scores else 0.0

                return min(1.0, avg_relevance)

            elif signal_type == "company_metadata":
                # Quality based on completeness of company data
                if isinstance(data, dict):
                    completeness = sum(1 for v in data.values() if v) / len(data)
                    return min(1.0, completeness)
                return 0.5

            return 0.5  # Default neutral quality

        except Exception as e:
            logger.error("Signal quality evaluation failed", error=str(e))
            return 0.0

    async def _update_feedback_memory(self, tool_name: str, result_data: Any,
                                    latency: float, signal_quality: float):
        """Update feedback memory for learning."""
        try:
            # This would update the APIFeedback table in production
            # For now, we'll update in-memory cache
            feedback_key = f"feedback_stats:{tool_name}"

            current_stats = await cache.get(feedback_key) or {
                "total_calls": 0,
                "successful_calls": 0,
                "total_latency": 0.0,
                "total_signal_quality": 0.0
            }

            current_stats["total_calls"] += 1
            if result_data:  # Consider it successful if we got data
                current_stats["successful_calls"] += 1
            current_stats["total_latency"] += latency
            current_stats["total_signal_quality"] += signal_quality

            await cache.set(feedback_key, current_stats, ttl=86400)  # 24 hours

        except Exception as e:
            logger.error("Feedback memory update failed", error=str(e))

    def _calculate_confidence(self, state: Dict[str, Any]) -> float:
        """Calculate overall confidence based on evidence collected."""
        try:
            evidence_count = len(state.get("evidence_objects", []))
            avg_signal_quality = np.mean([
                step["signal_quality"] for step in state.get("execution_history", [])
                if step["success"]
            ]) if state.get("execution_history") else 0.0

            # Simple confidence model: evidence count + average quality
            confidence = min(1.0, (evidence_count * 0.1) + avg_signal_quality)
            return confidence

        except Exception as e:
            logger.error("Confidence calculation failed", error=str(e))
            return 0.0

    def _create_intent_signature(self, concept_vector: Dict[str, float]) -> str:
        """Create a signature for the intent based on concept vector."""
        # Simple hash of rounded concept values
        signature_parts = [f"{k}:{v:.1f}" for k, v in sorted(concept_vector.items())]
        return hashlib.md5("|".join(signature_parts).encode()).hexdigest()

    # Tool execution functions
    async def _execute_arbeitnow_search(self, constraints: Dict[str, Any], state: Dict[str, Any]) -> Any:
        """Execute Arbeitnow job search."""
        role = constraints.get("role", "")
        region = constraints.get("region", "")
        return await job_api_manager.fetch_arbeitnow_jobs(query=role, location=region)

    async def _execute_github_search(self, constraints: Dict[str, Any], state: Dict[str, Any]) -> Any:
        """Execute GitHub job search."""
        role = constraints.get("role", "")
        region = constraints.get("region", "")
        return await job_api_manager.fetch_github_jobs(description=role, location=region)

    async def _execute_news_search(self, constraints: Dict[str, Any], state: Dict[str, Any]) -> Any:
        """Execute company news search."""
        # This would need company names from previous evidence
        # For now, return empty result
        return {"news": [], "total_count": 0, "source": "news_api"}

    async def _execute_metadata_search(self, constraints: Dict[str, Any], state: Dict[str, Any]) -> Any:
        """Execute company metadata search."""
        # This would need company names from previous evidence
        # For now, return empty result
        return {"companies": [], "total_count": 0, "source": "metadata_api"}


# Global action orchestrator instance
action_orchestrator = ActionOrchestrator()
