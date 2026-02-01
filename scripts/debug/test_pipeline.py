"""Test the entire job search pipeline end-to-end."""
import sys
sys.path.insert(0, '.')

import asyncio
from app.apis.job_apis import job_api_manager

async def test_pipeline():
    # 1. Test RemoteOK directly
    print("=== STEP 1: Fetching from RemoteOK ===")
    result = await job_api_manager.fetch_remoteok_jobs(query="data", limit=10)
    print(f"RemoteOK returned: {result['total_count']} jobs")
    
    if result['jobs']:
        print(f"Sample job: {result['jobs'][0]}")
    
    # 2. Test the full search_jobs method
    print("\n=== STEP 2: Testing full search_jobs ===")
    constraints = {"role": "data scientist", "location": "remote"}
    jobs = await job_api_manager.search_jobs(constraints)
    print(f"search_jobs returned: {len(jobs)} jobs")
    
    if jobs:
        print(f"Sample job: {jobs[0]}")
        
    # 3. Test normalization
    print("\n=== STEP 3: Testing normalization ===")
    from app.search.lead_normalizer import LeadNormalizer
    
    if jobs:
        normalized = LeadNormalizer.batch_normalize(jobs)
        print(f"Normalized leads: {len(normalized)}")
        if normalized:
            print(f"Sample lead: {normalized[0].to_dict()}")
    else:
        print("No jobs to normalize!")

asyncio.run(test_pipeline())
