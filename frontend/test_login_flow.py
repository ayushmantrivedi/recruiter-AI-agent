#!/usr/bin/env python3
"""Test the frontend login flow."""

import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

FRONTEND_URL = "http://localhost:3001"

def test_login_flow():
    """Test the complete login flow."""
    print("=== TESTING LOGIN FLOW ===")

    # Set up Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,720")

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(FRONTEND_URL)

        print("[OK] Browser opened, navigating to frontend")

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        print(f"[OK] Page loaded, title: {driver.title}")

        # Check if we're on login page
        page_content = driver.page_source
        if "Sign in to Recruiter AI" in page_content:
            print("[OK] On login page")

            # Check if recruiter ID checkbox is checked by default
            checkbox = driver.find_element(By.ID, "useRecruiterId")
            if checkbox.is_selected():
                print("[OK] Recruiter ID mode is enabled by default")
            else:
                print("[WARNING] Recruiter ID mode not enabled, enabling it")
                checkbox.click()

            # Check if recruiter ID input has value "2"
            recruiter_input = driver.find_element(By.ID, "recruiterId")
            current_value = recruiter_input.get_attribute("value")
            print(f"[INFO] Recruiter ID input value: '{current_value}'")

            if current_value != "2":
                recruiter_input.clear()
                recruiter_input.send_keys("2")
                print("[OK] Set recruiter ID to '2'")

            # Submit the form
            submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()

            print("[OK] Login form submitted")

            # Wait for navigation or page change
            time.sleep(2)  # Give it a moment

            # Check current URL
            current_url = driver.current_url
            print(f"[INFO] Current URL after login: {current_url}")

            # Check page content
            new_content = driver.page_source

            if "Run AI Agent" in new_content:
                print("[SUCCESS] Successfully logged in and reached dashboard!")
                return True
            elif "Sign in to Recruiter AI" in new_content:
                print("[ERROR] Still on login page after submission")
                return False
            else:
                print(f"[ERROR] Unexpected page content: {new_content[:500]}...")
                return False

        else:
            print("[ERROR] Not on login page")
            print(f"Page content: {page_content[:500]}...")
            return False

    except Exception as e:
        print(f"[ERROR] Login flow test failed: {e}")
        return False
    finally:
        if driver:
            driver.quit()

def test_query_flow():
    """Test the query submission flow."""
    print("\n=== TESTING QUERY FLOW ===")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,720")

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(FRONTEND_URL)

        # Quick login
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "recruiterId"))
        )

        recruiter_input = driver.find_element(By.ID, "recruiterId")
        recruiter_input.clear()
        recruiter_input.send_keys("2")

        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()

        # Wait for dashboard
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "Run AI Agent")
        )

        print("[OK] Logged in successfully")

        # Navigate to run-agent page
        driver.get(f"{FRONTEND_URL}/run-agent")

        # Wait for query form
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "query"))
        )

        print("[OK] On run-agent page")

        # Fill and submit query
        query_input = driver.find_element(By.ID, "query")
        query_input.clear()
        query_input.send_keys("Find Python developers in Bangalore")

        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()

        print("[OK] Query submitted")

        # Wait for processing status
        WebDriverWait(driver, 10).until(
            EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "processing")
        )

        print("[OK] Processing status shown")

        # Wait for completion
        WebDriverWait(driver, 30).until(
            lambda d: "completed" in d.page_source or "Top Leads Found" in d.page_source
        )

        print("[SUCCESS] Query completed!")

        # Check for results
        if "Top Leads Found" in driver.page_source or "leads found" in driver.page_source:
            print("[SUCCESS] Results displayed!")
            return True
        else:
            print("[WARNING] Query completed but no results shown")
            return True

    except Exception as e:
        print(f"[ERROR] Query flow test failed: {e}")
        return False
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    # Test login flow
    login_success = test_login_flow()

    if login_success:
        # Test query flow
        query_success = test_query_flow()

        if query_success:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print("\n❌ QUERY FLOW FAILED")
    else:
        print("\n❌ LOGIN FLOW FAILED")