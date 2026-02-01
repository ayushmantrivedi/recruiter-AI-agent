"""Test the full orchestration pipeline including query parser."""
import sys
sys.path.insert(0, '.')

import asyncio
from app.search.search_orchestrator import SearchOrchestrator

async def test():
    print("=== Testing Full Orchestration ===")
    
    orchestrator = SearchOrchestrator()
    
    query = "senior data engineer with python"
    intelligence_data = {"intelligence": {}, "signals": {}}
    
    try:
        result = await orchestrator.orchestrate(query, intelligence_data)
        print(f"Success! Leads: {len(result.get('leads', []))}")
        print(f"Top companies: {result.get('top_companies', [])}")
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()

asyncio.run(test())
