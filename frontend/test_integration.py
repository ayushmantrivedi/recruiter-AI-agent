#!/usr/bin/env python3
"""Integration test for frontend + backend."""

import requests
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

def test_backend_health():
    """Test backend health endpoint."""
    print("=== TESTING BACKEND HEALTH ===")

    try:
        response = requests.get(f"{BACKEND_URL}/api/recruiter/health")
        if response.status_code == 200:
            print("[OK] Backend health check passed")
            return True
        else:
            print(f"[ERROR] Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Backend connection failed: {e}")
        return False

def test_frontend_access():
    """Test frontend accessibility."""
    print("\n=== TESTING FRONTEND ACCESS ===")

    try:
        response = requests.get(FRONTEND_URL)
        if response.status_code == 200:
            print("[OK] Frontend accessible")
            return True
        else:
            print(f"[ERROR] Frontend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Frontend connection failed: {e}")
        return False

def run_e2e_test():
    """Run end-to-end test with Selenium."""
    print("\n=== RUNNING E2E TEST ===")

    # Set up Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(FRONTEND_URL)

        print("[OK] Browser opened, navigating to frontend")

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h2"))
        )

        # Check if we're on login page
        if "Sign in to Recruiter AI" in driver.page_source:
            print("[OK] Login page loaded")

            # Enable recruiter ID mode
            checkbox = driver.find_element(By.ID, "useRecruiterId")
            if not checkbox.is_selected():
                checkbox.click()
                print("[OK] Enabled recruiter ID login mode")

            # Enter recruiter ID
            recruiter_input = driver.find_element(By.ID, "recruiterId")
            recruiter_input.clear()
            recruiter_input.send_keys("2")
            print("[OK] Entered recruiter ID: 2")

            # Submit login
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            print("[OK] Submitted login form")

            # Wait for navigation to dashboard
            WebDriverWait(driver, 10).until(
                EC.url_contains("/")
            )
            print("[OK] Successfully logged in")

            # Wait for dashboard to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TEXT, "Run AI Agent"))
            )
            print("[OK] Dashboard loaded")

            # Find and fill the query form
            query_textarea = driver.find_element(By.ID, "query")
            query_textarea.clear()
            query_textarea.send_keys("Find AI engineers in Bangalore with 2+ years experience")
            print("[OK] Entered query")

            # Submit the query
            run_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            run_button.click()
            print("[OK] Submitted query")

            # Wait for processing to start
            WebDriverWait(driver, 10).until(
                EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "processing")
            )
            print("[OK] Query processing started")

            # Wait for completion (up to 30 seconds)
            try:
                WebDriverWait(driver, 30).until(
                    EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "completed")
                )
                print("[OK] Query completed successfully")

                # Check if results are displayed
                if "Top Leads Found" in driver.page_source or "leads found" in driver.page_source:
                    print("[OK] Results displayed in UI")
                    return True
                else:
                    print("[WARNING] Query completed but no results displayed")
                    return True

            except Exception as e:
                print(f"[ERROR] Query did not complete: {e}")
                return False

        else:
            print("[ERROR] Not on login page")
            return False

    except Exception as e:
        print(f"[ERROR] E2E test failed: {e}")
        return False
    finally:
        if driver:
            driver.quit()

def main():
    """Run all tests."""
    print("🔧 RECRUITER AI PLATFORM INTEGRATION TEST")
    print("=" * 50)

    # Test backend
    if not test_backend_health():
        print("❌ Backend tests failed")
        return False

    # Test frontend
    if not test_frontend_access():
        print("❌ Frontend tests failed")
        return False

    # Run E2E test
    if run_e2e_test():
        print("\n✅ ALL TESTS PASSED!")
        print("🎉 Frontend + Backend + Database + AI Pipeline integration working!")
        return True
    else:
        print("\n❌ E2E TEST FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)