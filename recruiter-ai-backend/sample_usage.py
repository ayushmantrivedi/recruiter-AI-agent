#!/usr/bin/env python3
"""
Sample usage script for the Recruiter AI Platform.

This script demonstrates how to interact with the recruiter AI system
to process queries and get hiring leads.
"""

import asyncio
import json
import httpx
from typing import Dict, Any
import time


class RecruiterAIClient:
    """Simple client for interacting with the Recruiter AI API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """Check if the API is healthy."""
        response = await self.client.get(f"{self.base_url}/api/recruiter/health")
        response.raise_for_status()
        return response.json()

    async def process_query(self, query: str, recruiter_id: str = None) -> Dict[str, Any]:
        """Process a recruiter query."""
        payload = {"query": query}
        if recruiter_id:
            payload["recruiter_id"] = recruiter_id

        response = await self.client.post(
            f"{self.base_url}/api/recruiter/query",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    async def get_query_status(self, query_id: str) -> Dict[str, Any]:
        """Get the status of a query."""
        response = await self.client.get(f"{self.base_url}/api/recruiter/query/{query_id}")
        response.raise_for_status()
        return response.json()

    async def get_recruiter_stats(self, recruiter_id: str) -> Dict[str, Any]:
        """Get statistics for a recruiter."""
        response = await self.client.get(f"{self.base_url}/api/recruiter/stats/{recruiter_id}")
        response.raise_for_status()
        return response.json()

    async def submit_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Submit feedback on leads."""
        response = await self.client.post(
            f"{self.base_url}/api/recruiter/feedback",
            json=feedback
        )
        response.raise_for_status()
        return response.json()


async def demo_basic_usage():
    """Demonstrate basic usage of the Recruiter AI platform."""
    client = RecruiterAIClient()

    try:
        print("🤖 Recruiter AI Platform Demo")
        print("=" * 50)

        # 1. Health check
        print("\n1. Checking API health...")
        health = await client.health_check()
        print(f"✅ API Status: {health['status']}")
        print(f"📊 Version: {health['version']}")

        # 2. Sample queries to demonstrate
        sample_queries = [
            "Find senior backend engineers in Bangalore urgently",
            "Remote frontend developers with React experience",
            "Data scientists for machine learning roles",
            "DevOps engineers for cloud infrastructure"
        ]

        for i, query in enumerate(sample_queries, 1):
            print(f"\n{i+1}. Processing query: '{query}'")

            # Submit query
            start_time = time.time()
            result = await client.process_query(query, recruiter_id="demo_recruiter")

            processing_time = time.time() - start_time

            if result["status"] == "completed":
                print(".2f"                print(f"🎯 Concept Analysis: {result['concept_vector']}")
                print(f"📋 Constraints: {result['constraints']}")
                print(f"📊 Orchestration: {result['orchestration_summary']}")

                # Show top leads
                leads = result["leads"][:3]  # Show top 3
                if leads:
                    print(f"🏆 Top {len(leads)} Leads:")
                    for j, lead in enumerate(leads, 1):
                        print(f"  {j}. {lead['company']} (Score: {lead['score']})")
                        print(f"     Reasons: {', '.join(lead['reasons'][:2])}")
                else:
                    print("   No leads found (this is normal for demo without real APIs)")

            elif result["status"] == "processing":
                query_id = result["query_id"]
                print(f"⏳ Query processing in background (ID: {query_id})")

                # Wait a bit and check status
                await asyncio.sleep(2)
                status = await client.get_query_status(query_id)
                print(f"📊 Status: {status.get('status', 'unknown')}")

        # 3. Get recruiter statistics
        print("
4. Getting recruiter statistics...")
        try:
            stats = await client.get_recruiter_stats("demo_recruiter")
            print(f"📈 Total Queries: {stats['total_queries']}")
            print(f"🎯 Total Leads: {stats['total_leads']}")
            print(f"📊 Average Lead Score: {stats['average_lead_score']}")
            print(f"💰 Total Cost: ${stats['total_cost']}")
        except Exception as e:
            print(f"Note: Statistics not available yet: {e}")

        # 4. Submit sample feedback
        print("
5. Submitting feedback...")
        try:
            feedback = {
                "query_id": "demo_query_123",
                "company": "TechCorp",
                "rating": 4,
                "feedback_type": "lead_quality",
                "comments": "Good lead, company is actively hiring"
            }
            response = await client.submit_feedback(feedback)
            print(f"✅ Feedback submitted: {response['message']}")
        except Exception as e:
            print(f"Note: Feedback submission failed: {e}")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("\nMake sure the API is running:")
        print("  docker-compose up -d")
        print("  # or")
        print("  python -m uvicorn app.main:app --reload")

    finally:
        await client.close()


async def demo_advanced_usage():
    """Demonstrate advanced usage patterns."""
    client = RecruiterAIClient()

    try:
        print("\n🔬 Advanced Usage Demo")
        print("=" * 30)

        # Analyze concept extraction for different query types
        queries_and_expected = [
            ("URGENT: Need senior developers NOW", {"hiring_pressure": "high"}),
            ("Looking for rare blockchain experts", {"role_scarcity": "high"}),
            ("Replace contractor with full-time hire", {"outsourcing_likelihood": "high"}),
            ("Entry-level positions for graduates", {"hiring_pressure": "low"})
        ]

        print("\n🧠 Concept Analysis Examples:")
        for query, expected in queries_and_expected:
            try:
                result = await client.process_query(query)
                if result["status"] == "completed":
                    concepts = result["concept_vector"]
                    print(f"\nQuery: '{query}'")
                    print(f"Expected: {expected}")
                    print(f"Detected: Hiring Pressure: {concepts['hiring_pressure']:.2f}, "
                          f"Role Scarcity: {concepts['role_scarcity']:.2f}, "
                          f"Outsourcing: {concepts['outsourcing_likelihood']:.2f}")
            except Exception as e:
                print(f"Query failed: {e}")

    finally:
        await client.close()


async def main():
    """Main demo function."""
    print("🚀 Recruiter AI Platform - Interactive Demo")
    print("This demo shows how recruiters can use the AI system to find hiring leads.\n")

    # Basic usage demo
    await demo_basic_usage()

    # Advanced usage demo
    await demo_advanced_usage()

    print("
🎉 Demo completed!")
    print("
Next steps:")
    print("1. Check the API documentation at http://localhost:8000/docs")
    print("2. Explore the code in the app/ directory")
    print("3. Run the test suite: pytest tests/")
    print("4. Deploy to production: docker-compose up -d")


if __name__ == "__main__":
    asyncio.run(main())
