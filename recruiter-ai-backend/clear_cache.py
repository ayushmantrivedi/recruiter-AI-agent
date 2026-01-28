import asyncio
import os
from app.utils.cache import cache

async def clear_cache():
    # Setup environment
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    
    await cache.connect()
    # Replace with the query IDs that might be stuck
    stuck_ids = [
        "39f7d9a6-4fe2-4544-b9a0-423f7c5fdafb",
        "f49e91c6-8098-49a7-88aa-d4e69afaa7db"
    ]
    
    for qid in stuck_ids:
        key = f"query_result:{qid}"
        await cache.delete(key)
        print(f"Cleared cache for {key}")
        
    await cache.disconnect()

if __name__ == "__main__":
    asyncio.run(clear_cache())
