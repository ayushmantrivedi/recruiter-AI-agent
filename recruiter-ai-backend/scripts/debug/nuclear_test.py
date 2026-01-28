"""
Nuclear Debug Test - Run the full pipeline purely in python to see the traceback.
"""
import sys
import asyncio
import traceback
import os

# Ensure we can import app modules
sys.path.insert(0, os.getcwd())

from dotenv import load_dotenv
load_dotenv()

async def run_nuclear_test():
    print("☢️ STARTING NUCLEAR TEST ☢️")
    try:
        from app.services.pipeline import recruiter_pipeline
        
        query = "senior data scientist salary"
        recruiter_id = "nuclear_debug"
        
        print(f"1. Initialized Pipeline. Processing query: '{query}'")
        
        # Call the exact method the route calls
        result = await recruiter_pipeline.process_recruiter_query(
            recruiter_query=query, 
            recruiter_id=recruiter_id
        )
        
        print("\n✅ SUCCESS! Result keys:", result.keys())
        if result.get("leads"):
            print(f"Found {len(result['leads'])} leads.")
        else:
            print("No leads found, but no crash.")
            
    except Exception as e:
        print("\n❌ CRITICAL FAILURE ❌")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(run_nuclear_test())
    except KeyboardInterrupt:
        pass
