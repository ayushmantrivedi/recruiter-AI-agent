import requests
import time
import json
import statistics

BASE_URL = "http://localhost:8000"
IDENTITY = "real_user_001"
QUERIES = [
    "Senior Python Developer in London with Django",
    "Marketing Manager in New York"
]

def print_section(title):
    print(f"\n{'='*50}")
    print(f"USER ACTION: {title}")
    print(f"{'='*50}")

def run_simulation():
    session = requests.Session()
    session_data = {"timings": []}

    # 1. Login
    print_section("Logging In")
    try:
        t0 = time.time()
        resp = session.post(f"{BASE_URL}/auth/identity", json={"identity": IDENTITY})
        latency = time.time() - t0
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            session.headers.update({"Authorization": f"Bearer {token}"})
            print(f"✅ Login Successful (Latency: {latency:.2f}s)")
        else:
            print(f"❌ Login Failed: {resp.text}")
            return
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 2. Perform Searches
    for query in QUERIES:
        print_section(f"Searching: '{query}'")
        try:
            # Submit
            t0 = time.time()
            resp = session.post(f"{BASE_URL}/api/recruiter/query", json={"query": query})
            if resp.status_code != 200:
                print(f"❌ Submission Failed: {resp.text}")
                continue
            
            query_id = resp.json()["query_id"]
            print(f"ℹ️  Query ID: {query_id}")

            # Poll
            while True:
                status_resp = session.get(f"{BASE_URL}/api/recruiter/query/{query_id}")
                data = status_resp.json()
                status = data["status"]
                
                if status == "completed":
                    total_time = time.time() - t0
                    session_data["timings"].append(total_time)
                    
                    leads = data.get("leads", [])
                    print(f"✅ Search Completed in {total_time:.2f}s")
                    print(f"📊 Leads Found: {len(leads)}")
                    print(f"🔎 Sources Called: {data.get('orchestration_summary', {}).get('providers_called', 'N/A')}")
                    
                    if leads:
                        print("🏆 Top Candidate:")
                        top = leads[0]
                        print(f"   Name: {top.get('title', 'Unknown')} at {top.get('company', 'Unknown')}")
                        print(f"   Source: {top.get('source', 'Unknown')}")
                        print(f"   URL: {top.get('url', 'Unknown')}")
                    break
                
                if status == "failed":
                    print(f"❌ Search Failed: {data.get('error')}")
                    break
                
                time.sleep(1)
        except Exception as e:
            print(f"❌ Error during search: {e}")

    # 3. Check History/Stats
    print_section("Checking History & Stats")
    try:
        resp = session.get(f"{BASE_URL}/api/recruiter/stats/{IDENTITY}")
        if resp.status_code == 200:
            stats = resp.json()
            print("✅ Stats Retrieved:")
            print(json.dumps(stats, indent=2))
        else:
            print(f"❌ Stats Retrieval Failed: {resp.text}")
    except Exception as e:
        print(f"❌ Error fetching stats: {e}")

    # Summary
    print_section("Session Summary")
    if session_data["timings"]:
        avg_time = statistics.mean(session_data["timings"])
        print(f"Average Search Time: {avg_time:.2f}s")
    print("User Journey Simulation Complete.")

if __name__ == "__main__":
    run_simulation()
