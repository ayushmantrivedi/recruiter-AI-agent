import sys
import os

try:
    from app.search.search_orchestrator import search_orchestrator
    print("SUCCESS: SearchOrchestrator imported")
except Exception as e:
    import traceback
    traceback.print_exc()
