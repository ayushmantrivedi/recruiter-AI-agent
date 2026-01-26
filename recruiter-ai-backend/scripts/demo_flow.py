
import requests
import time
import sys
import json

BASE_URL = "http://localhost:8001/api/recruiter"

def run_demo():
    print(f"🚀 Connecting to Recruiter AI at {BASE_URL}...")
    
    # 1. Submit Query
    query = "Senior Backend Engineer with Python and AWS experience"
    print(f"\n📨 Submitting Query: '{query}'")
    
    try:
        resp = requests.post(f"{BASE_URL}/query", json={"query": query})
        resp.raise_for_status()
        data = resp.json()
        query_id = data["query_id"]
        print(f"✅ Job Accepted! ID: {query_id}")
    except Exception as e:
        print(f"❌ Failed to submit: {e}")
        return

    # 2. Poll
    print("\n⏳ Polling for results...")
    while True:
        try:
            r = requests.get(f"{BASE_URL}/query/{query_id}")
            r.raise_for_status()
            result = r.json()
            status = result["status"]
            
            if status == "completed":
                print(f"✅ Status: {status}")
                display_results(result)
                break
            elif status == "failed":
                print(f"❌ Status: {status} - {result.get('error')}")
                break
            else:
                print(f"   Status: {status}...", end="\r")
                time.sleep(1.0)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user.")
            break
        except Exception as e:
            print(f"\n❌ Error polling: {e}")
            break

def display_results(result):
    print("\n" + "="*60)
    print("🤖 AI EXECUTIVE BRIEFING")
    print("="*60 + "\n")
    
    report = result.get("synthesis_report")
    if report:
        print(report)
    else:
        print("(No synthesis report generated)")
        
    print("\n" + "-"*60)
    print("📋 DATA SUMMARY")
    print("-"*60)
    print(f"Total Found: {result.get('total_leads_found')}")
    print(f"Strategies Used: {result.get('orchestration_summary', {}).get('execution_mode', 'N/A')}")
    print(f"Top Candidate: {result['leads'][0]['company'] if result['leads'] else 'None'}")

if __name__ == "__main__":
    run_demo()
