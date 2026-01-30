import requests
import json
import time

base_url = "http://localhost:8000"

def test_full_flow(identity):
    print(f"\n--- Testing Flow for: {identity} ---")
    
    # 1. Login
    login_url = f"{base_url}/auth/identity"
    payload = {"identity": identity}
    try:
        login_resp = requests.post(login_url, json=payload)
        if login_resp.status_code != 200:
            print(f"Login failed: {login_resp.status_code} - {login_resp.text}")
            return
        
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("Login success, token obtained.")
        
        # 2. Test Query Execution
        print("Testing query execution...")
        query_url = f"{base_url}/api/recruiter/query"
        query_payload = {"query": "Find software engineers in San Francisco"}
        query_resp = requests.post(query_url, json=query_payload, headers=headers)
        
        if query_resp.status_code != 200:
            print(f"Query submission failed: {query_resp.status_code} - {query_resp.text}")
            return
            
        query_id = query_resp.json()["query_id"]
        print(f"Query submitted successfully. ID: {query_id}")
        
        # 3. Poll for status
        print("Polling for status...")
        for i in range(20):  # 60 seconds total
            status_url = f"{base_url}/api/recruiter/query/{query_id}"
            status_resp = requests.get(status_url, headers=headers)
            
            if status_resp.status_code != 200:
                print(f"Status check failed: {status_resp.status_code} - {status_resp.text}")
                break
                
            data = status_resp.json()
            status = data.get("status")
            leads_found = data.get("total_leads_found", 0)
            print(f"  Attempt {i+1}: Status={status}, Leads={leads_found}")
            
            if status == "completed":
                print("✅ Query completed successfully!")
                return
            elif status == "failed":
                print(f"❌ Query failed: {data.get('error')}")
                return
                
            time.sleep(3)
            
        print("⏰ Timed out waiting for query completion.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_full_flow("julie")
