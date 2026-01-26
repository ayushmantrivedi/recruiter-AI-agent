
import asyncio
import sys
import os
import json

import sys
import os

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__)) # scripts/debug
scripts_dir = os.path.dirname(current_dir) # scripts
project_root = os.path.dirname(scripts_dir) # recruiter-ai-backend
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# import params # Removed


from app.agents.synthesis_agent import synthesis_agent

async def test_synthesis():
    print("🤖 --- RECRUITER AI: SYNTHESIS AGENT TEST ---\n")
    
    # 1. Mock Data (Simulating a "Previous Log" / DB Result)
    query_text = "Senior iOS Engineer with Fintech experience"
    query_id = "test-run-001"
    
    logger_context = {
        "raw_leads_found": 142,
        "execution_mode": "DEEP_SEARCH",
        "providers_called": ["arbeitnow", "github_jobs", "google_search"]
    }
    
    leads = [
        {
            "company": "Fintorex",
            "score": 92.5,
            "reasons": [
                "Strong Fintech keywords in description",
                "Mention of 'high-frequency trading'",
                "Recent Series B funding news ($50M)"
            ]
        },
        {
            "company": "PayStream",
            "score": 88.0,
            "reasons": [
                "Payments processing domain",
                "Active 'iOS Lead' posting",
                "Matches location preference (London/Remote)"
            ]
        },
        {
            "company": "Bankify",
            "score": 75.0,
            "reasons": [
                "Legacy banking integration mentioned",
                "Hiring aggressively (14 open roles)"
            ]
        }
    ]
    
    print(f"INPUT QUERY: {query_text}")
    print(f"FOUND: {len(leads)} leads (from {logger_context['raw_leads_found']} raw)")
    print("-" * 50)
    
    # 2. Run Agent
    briefing = await synthesis_agent.generate_briefing(
        query_id=query_id,
        query_text=query_text,
        leads=leads,
        orchestration_summary=logger_context
    )
    
    # 3. Output
    print("\n📝 GENERATED BRIEFING:\n")
    print(briefing)
    print("\n" + "-" * 50)

if __name__ == "__main__":
    asyncio.run(test_synthesis())
