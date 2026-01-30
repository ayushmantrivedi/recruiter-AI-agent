import asyncio
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

from app.search.search_orchestrator import SearchOrchestrator
from app.database import SessionLocal, Lead, Query
from app.config import settings

async def debug_search():
    print("Initializing SearchOrchestrator...")
    orchestrator = SearchOrchestrator()
    
    query_text = "Python Developer in Berlin"
    constraints = {"role": "Python Developer", "location": "Berlin"}
    
    print(f"Executing search for: {query_text}")
    results = await orchestrator.orchestrate(query_text, constraints)
    
    leads = results["leads"]
    report = results["execution_report"]
    
    print(f"Orchestrator returned {len(leads)} leads.")
    print(f"Execution Report: Raw={report.raw_leads_found}, Ranked={report.ranked_leads_count}, Dedup={report.deduplicated_count}")
    
    # Check if they are deduplicated
    from collections import Counter
    companies = [l.get("company_name", "Unknown") for l in leads]
    dist = Counter(companies)
    print(f"Full Company distribution: {dist}")
    
    # Assert density control
    for company, count in dist.items():
        if count > 3:
            print(f"FAILURE: Company {company} has {count} leads (Limit is 3)")
        else:
            print(f"SUCCESS: {company} -> {count}")
    
    # Print sample
    for i, lead in enumerate(leads[:10]):
        print(f"{i+1}. {lead['company_name']} | {lead['role']} | {lead.get('location', 'N/A')} | {lead.get('score', 0)}")

if __name__ == "__main__":
    asyncio.run(debug_search())
