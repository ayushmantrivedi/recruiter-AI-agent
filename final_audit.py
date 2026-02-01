import sqlite3
import pandas as pd

DB_PATH = "recruiter_ai.db"

def final_audit():
    print("--- FINAL BEST-IN-CLASS QUALITY AUDIT ---")
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Total Leads
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]
    print(f"Total Leads Found: {total}")
    
    # 2. Results per company
    print("\n[Leads per Company - Limits Check (Max 3)]")
    counts = pd.read_sql_query("SELECT company_name, COUNT(*) as cnt FROM leads GROUP BY company_name ORDER BY cnt DESC LIMIT 10", conn)
    print(counts.to_string(index=False))
    
    # Check if any company exceeds 3
    over_limit = counts[counts['cnt'] > 3]
    if not over_limit.empty:
        print("\nWARNING: Density limit BREACHED!")
    else:
        print("\nSUCCESS: All companies within density limits.")

    # 3. Cleanliness check (No GmbH/AG in grouping)
    print("\n[Company Name Cleanliness]")
    companies = pd.read_sql_query("SELECT DISTINCT company_name FROM leads LIMIT 10", conn)
    print(companies.to_string(index=False))
    
    conn.close()

if __name__ == "__main__":
    final_audit()
