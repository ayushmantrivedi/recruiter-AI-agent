#!/usr/bin/env python3
"""Test pipeline get_query_status directly."""

import sys
import asyncio
sys.path.append('.')

from app.services.pipeline import recruiter_pipeline

async def test_pipeline():
    query_id = "8196d517-7c23-4b3f-8fac-efd5d99725cc"
    print(f"Testing pipeline.get_query_status for {query_id}")

    result = await recruiter_pipeline.get_query_status(query_id)
    print(f"Result: {result}")

    if result:
        print("SUCCESS: Pipeline found the query")
    else:
        print("ERROR: Pipeline did not find the query")

if __name__ == "__main__":
    asyncio.run(test_pipeline())