import httpx
import asyncio
import time

async def trigger_search():
    url = "http://localhost:8000/ui/query"
    data = {
        "query": "Backend Engineer in Munich",
        "recruiter_id": "verified_user"
    }
    
    print(f"Triggering search: {data['query']}")
    async with httpx.AsyncClient() as client:
        # The UI endpoint expects form data
        resp = await client.post(url, data=data)
        print(f"Status: {resp.status_code}")
        
    print("Waiting 10s for processing...")
    time.sleep(10)
    print("Done.")

if __name__ == "__main__":
    asyncio.run(trigger_search())
