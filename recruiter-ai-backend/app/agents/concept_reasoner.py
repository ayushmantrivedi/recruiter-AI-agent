import json
from typing import Dict, Any, List, Optional
import hashlib
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from openai import AsyncOpenAI
import numpy as np
from ..config import settings
from ..utils.logger import get_logger, log_concept_inference
from ..utils.cache import cache

logger = get_logger("concept_reasoner")


class ConceptReasoner:
    """Concept Reasoner agent using LCM + MLM behavior.

    Converts vague recruiter intent into explicit concept constraints
    using masked language models and LLM reasoning.
    """

    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.openai_client = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    async def initialize(self):
        """Initialize ML models and clients."""
        try:
            # Initialize HuggingFace model for MLM embeddings
            model_name = settings.agent.concept_model_name
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name).to(self.device)
            self.model.eval()

            # Initialize OpenAI client if API key available
            if settings.api.openai_api_key:
                self.openai_client = AsyncOpenAI(
                    api_key=settings.api.openai_api_key.get_secret_value()
                )

            logger.info("Concept Reasoner initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Concept Reasoner", error=str(e))
            raise

    async def process_query(self, query_text: str, recruiter_id: str = None) -> Dict[str, Any]:
        """Process recruiter query into concept constraints.

        Args:
            query_text: Raw recruiter search query
            recruiter_id: Optional recruiter ID for personalization

        Returns:
            Dictionary containing concept_vector and constraints
        """
        try:
            # Check cache first
            query_hash = hashlib.md5(query_text.encode()).hexdigest()
            cached_result = await cache.get_concept_vector(query_hash)
            if cached_result:
                logger.info("Using cached concept vector", query_hash=query_hash)
                return cached_result

            # Extract concept vector using MLM
            concept_vector = await self._extract_concepts(query_text)

            # Generate constraints using LLM reasoning
            constraints = await self._generate_constraints(query_text, concept_vector)

            # Create result
            result = {
                "concept_vector": concept_vector,
                "constraints": constraints
            }

            # Cache result
            await cache.save_concept_vector(query_hash, result, ttl=3600)

            # Log inference
            log_concept_inference(
                query_id=query_hash,
                concept_vector=concept_vector,
                constraints=constraints
            )

            return result

        except Exception as e:
            logger.error("Concept reasoning failed", error=str(e), query=query_text)
            raise

    async def _extract_concepts(self, query_text: str) -> Dict[str, float]:
        """Extract concept vector using masked language model embeddings.

        Focuses on:
        - hiring_pressure: Urgency indicators
        - role_scarcity: How hard it is to find this role
        - outsourcing_likelihood: Probability of using staffing agencies
        """
        try:
            # Define concept templates for MLM scoring
            concept_templates = {
                "hiring_pressure": [
                    "We need to hire [MASK] immediately",
                    "Urgent requirement for [MASK] position",
                    "Critical hiring need for [MASK] role",
                    "Must fill [MASK] position ASAP"
                ],
                "role_scarcity": [
                    "Hard to find qualified [MASK] candidates",
                    "Scarce [MASK] talent in the market",
                    "Competitive market for [MASK] skills",
                    "Limited pool of [MASK] professionals"
                ],
                "outsourcing_likelihood": [
                    "Consider staffing agencies for [MASK]",
                    "May need recruiters for [MASK] search",
                    "External hiring help for [MASK] position",
                    "Contingency search for [MASK] role"
                ]
            }

            concept_scores = {}

            # Process each concept
            for concept_name, templates in concept_templates.items():
                template_scores = []

                for template in templates:
                    # Replace [MASK] with query terms
                    masked_text = template.replace("[MASK]", query_text.lower())

                    # Get embeddings
                    inputs = self.tokenizer(masked_text, return_tensors="pt", padding=True, truncation=True)
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}

                    with torch.no_grad():
                        outputs = self.model(**inputs)
                        embeddings = outputs.last_hidden_state.mean(dim=1)

                    # Score based on embedding confidence (simplified)
                    # In production, you'd use more sophisticated scoring
                    score = float(torch.sigmoid(embeddings.mean()).item())
                    template_scores.append(score)

                # Average template scores for concept
                concept_scores[concept_name] = float(np.mean(template_scores))

            # Normalize scores to 0-1 range
            for concept in concept_scores:
                concept_scores[concept] = min(1.0, max(0.0, concept_scores[concept]))

            logger.info("Concept extraction completed", scores=concept_scores)
            return concept_scores

        except Exception as e:
            logger.error("Concept extraction failed", error=str(e))
            # Return default neutral scores
            return {
                "hiring_pressure": 0.5,
                "role_scarcity": 0.5,
                "outsourcing_likelihood": 0.5
            }

    async def _generate_constraints(self, query_text: str, concept_vector: Dict[str, float]) -> Dict[str, Any]:
        """Generate explicit constraints using LLM reasoning."""

        if not self.openai_client:
            # Fallback to rule-based constraints if no OpenAI
            return self._rule_based_constraints(query_text, concept_vector)

        try:
            prompt = f"""
            Analyze this recruiter search query and extract structured constraints.
            Focus on role, location, company size, and time windows.

            Query: "{query_text}"

            Concept Analysis:
            - Hiring Pressure: {concept_vector['hiring_pressure']:.2f}
            - Role Scarcity: {concept_vector['role_scarcity']:.2f}
            - Outsourcing Likelihood: {concept_vector['outsourcing_likelihood']:.2f}

            Return ONLY a JSON object with this exact structure:
            {{
                "role": "extracted role or null",
                "region": "location preference or 'remote'",
                "min_job_posts": 1-10 (based on scarcity),
                "window_days": 7-90 (based on pressure),
                "exclude_enterprise": true/false (based on outsourcing likelihood)
            }}
            """

            response = await self.openai_client.chat.completions.create(
                model=settings.agent.reasoning_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )

            result_text = response.choices[0].message.content.strip()

            # Parse JSON response
            try:
                constraints = json.loads(result_text)
                logger.info("LLM constraints generated", constraints=constraints)
                return constraints
            except json.JSONDecodeError:
                logger.warning("LLM returned invalid JSON, using fallback")
                return self._rule_based_constraints(query_text, concept_vector)

        except Exception as e:
            logger.error("LLM reasoning failed", error=str(e))
            return self._rule_based_constraints(query_text, concept_vector)

    def _rule_based_constraints(self, query_text: str, concept_vector: Dict[str, float]) -> Dict[str, Any]:
        """Fallback rule-based constraint extraction."""

        # Simple keyword extraction
        query_lower = query_text.lower()

        # Role extraction
        role_keywords = {
            "backend": ["backend", "back-end", "server", "api"],
            "frontend": ["frontend", "front-end", "ui", "ux", "react", "angular"],
            "fullstack": ["fullstack", "full-stack", "full stack"],
            "devops": ["devops", "sre", "infrastructure", "cloud"],
            "data": ["data scientist", "machine learning", "ml", "ai", "analytics"]
        }

        role = None
        for role_name, keywords in role_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                role = role_name
                break

        # Location extraction
        location_keywords = {
            "remote": ["remote", "work from home"],
            "india": ["india", "indian"],
            "us": ["us", "usa", "united states"],
            "europe": ["europe", "eu", "germany", "uk"]
        }

        region = "remote"  # default
        for loc_name, keywords in location_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                region = loc_name
                break

        # Dynamic constraints based on concept scores
        pressure = concept_vector["hiring_pressure"]
        scarcity = concept_vector["role_scarcity"]
        outsourcing = concept_vector["outsourcing_likelihood"]

        constraints = {
            "role": role,
            "region": region,
            "min_job_posts": max(1, int(scarcity * 10)),  # 1-10 based on scarcity
            "window_days": max(7, int(pressure * 90)),    # 7-90 days based on pressure
            "exclude_enterprise": outsourcing > 0.7        # Exclude enterprise if high outsourcing likelihood
        }

        logger.info("Rule-based constraints generated", constraints=constraints)
        return constraints


# Global concept reasoner instance
concept_reasoner = ConceptReasoner()
