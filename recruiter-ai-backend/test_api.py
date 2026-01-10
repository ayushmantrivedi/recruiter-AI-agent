#!/usr/bin/env python3
"""Test the recruiter API endpoints."""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_post_query():
    """Test POST /api/recruiter/query endpoint."""
    print("=== TESTING POST /api/recruiter/query ===")

    payload = {
        "query": "Find senior Python developers in Bangalore"
        # "recruiter_id": "test_recruiter_123"  # Commented out to avoid foreign key issues
    }

    try:
        response = requests.post(f"{BASE_URL}/api/recruiter/query", json=payload)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("Response:")
            print(json.dumps(result, indent=2))

            # Check if we got a real UUID
            query_id = result.get('query_id')
            if query_id and query_id != 'pending' and len(query_id) == 36:
                print(f"[OK] Got real UUID: {query_id}")
                return query_id
            else:
                print(f"[ERROR] Invalid query_id: {query_id}")
                return None
        else:
            print(f"[ERROR] Request failed: {response.text}")
            return None

    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return None

def test_get_result(query_id):
    """Test GET /api/recruiter/query/{query_id} endpoint."""
    print(f"\n=== TESTING GET /api/recruiter/query/{query_id} ===")

    max_attempts = 30  # 30 seconds max
    attempt = 0

    while attempt < max_attempts:
        try:
            response = requests.get(f"{BASE_URL}/api/recruiter/query/{query_id}")
            print(f"Attempt {attempt + 1}: Status Code {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                print(f"Job status: {status}")

                if status == 'completed':
                    print("[OK] Job completed!")
                    print("Result summary:")
                    print(f"  - Query: {result.get('original_query')}")
                    print(f"  - Leads found: {result.get('total_leads_found')}")
                    print(f"  - Processing time: {result.get('processing_time')}")
                    return True
                elif status == 'processing':
                    print("[OK] Job still processing...")
                    time.sleep(1)
                    attempt += 1
                elif status == 'failed':
                    print(f"[ERROR] Job failed: {result.get('error')}")
                    return False
                else:
                    print(f"[ERROR] Unknown status: {status}")
                    return False
            else:
                print(f"[ERROR] Request failed: {response.text}")
                return False

        except Exception as e:
            print(f"[ERROR] Request failed: {e}")
            return False

    print("[ERROR] Job did not complete within timeout")
    return False

def test_health():
    """Test health endpoint."""
    print("\n=== TESTING HEALTH ENDPOINT ===")

    try:
        response = requests.get(f"{BASE_URL}/api/recruiter/health")
        if response.status_code == 200:
            print("[OK] Health endpoint working")
            return True
        else:
            print(f"[ERROR] Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Health check failed: {e}")
        return False

if __name__ == "__main__":
    # Test health first
    if not test_health():
        print("Health check failed, exiting")
        exit(1)

    # Test job creation
    query_id = test_post_query()
    if not query_id:
        print("Job creation failed, exiting")
        exit(1)

    # Test job completion
    success = test_get_result(query_id)
    if success:
        print("\n[SUCCESS] Full job lifecycle test passed!")
    else:
        print("\n[FAILED] Job lifecycle test failed!")
        exit(1)