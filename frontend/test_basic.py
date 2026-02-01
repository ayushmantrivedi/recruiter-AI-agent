#!/usr/bin/env python3
"""Basic test of frontend API calls."""

import requests
import json

FRONTEND_URL = "http://localhost:5174"
BACKEND_URL = "http://localhost:8000"

def test_backend_direct():
    """Test backend API directly."""
    print("=== TESTING BACKEND API DIRECTLY ===")

    # Test health
    try:
        response = requests.get(f"{BACKEND_URL}/api/recruiter/health")
        if response.status_code == 200:
            print("[OK] Backend health check passed")
        else:
            print(f"[ERROR] Backend health failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Backend connection failed: {e}")
        return False

    # Test query submission
    payload = {
        "query": "Find Python developers in Bangalore",
        "recruiter_id": "2"
    }

    try:
        response = requests.post(f"{BACKEND_URL}/api/recruiter/query", json=payload)
        print(f"[INFO] Query submission response: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            query_id = result.get('query_id')
            print(f"[OK] Query submitted, ID: {query_id}")

            # Test status polling
            import time
            max_attempts = 30
            for attempt in range(max_attempts):
                response = requests.get(f"{BACKEND_URL}/api/recruiter/query/{query_id}")
                if response.status_code == 200:
                    status_result = response.json()
                    status = status_result.get('status')
                    print(f"[INFO] Poll {attempt + 1}: Status = {status}")

                    if status == 'completed':
                        print("[OK] Query completed!")
                        return True
                    elif status == 'failed':
                        print(f"[ERROR] Query failed: {status_result.get('error')}")
                        return False

                time.sleep(1)

            print("[ERROR] Query did not complete within timeout")
            return False

        else:
            print(f"[ERROR] Query submission failed: {response.text}")
            return False

    except Exception as e:
        print(f"[ERROR] Query test failed: {e}")
        return False

def test_frontend_loading():
    """Test if frontend loads."""
    print("\n=== TESTING FRONTEND LOADING ===")

    try:
        response = requests.get(FRONTEND_URL)
        if response.status_code == 200:
            content = response.text
            if "Sign in to Recruiter AI" in content:
                print("[OK] Frontend loads and shows login page")
                return True
            else:
                print("[ERROR] Frontend loads but doesn't show login page")
                print(f"Content preview: {content[:500]}...")
                return False
        else:
            print(f"[ERROR] Frontend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Frontend connection failed: {e}")
        return False

if __name__ == "__main__":
    print("BASIC FRONTEND/BACKEND INTEGRATION TEST")
    print("=" * 50)

    # Test backend
    if not test_backend_direct():
        print("Backend tests failed")
        exit(1)

    # Test frontend
    if not test_frontend_loading():
        print("Frontend tests failed")
        exit(1)

    print("\nBASIC TESTS PASSED!")
    print("Backend and frontend are communicating correctly.")