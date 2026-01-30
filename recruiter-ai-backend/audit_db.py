import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "recruiter_ai.db"

def audit_database():
    print(f"--- DATABASE AUDIT: {datetime.now()} ---")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Total Counts
    cursor.execute("SELECT COUNT(*) FROM leads")
    total_leads = cursor.fetchone()[0]
    print(f"Total Leads: {total_leads}")
    
    # 2. Recent Leads (Last 20)
    print("\n[Last 20 Leads]")
    df = pd.read_sql_query("SELECT id, company_name as company, role as title, location, query_id, created_at FROM leads ORDER BY created_at DESC LIMIT 20", conn)
    print(df.to_string(index=False))
    
    # 3. Quality Check
    print("\n[Quality Issues]")
    cursor.execute("SELECT COUNT(*) FROM leads WHERE company_name='Unknown' OR company_name='Unknown Company'")
    unknown_companies = cursor.fetchone()[0]
    print(f"Leads with Unknown Company: {unknown_companies}")
    
    # source column removed from DB, skipping mock source check
    mock_leads = 0 
    print(f"Leads from Mock Sources: {mock_leads}")
    
    # 4. Duplicate Check (Naive)
    print("\n[Potential Duplicates]")
    dupes = pd.read_sql_query("SELECT company_name, role as title, COUNT(*) as cnt FROM leads GROUP BY company_name, role HAVING cnt > 1 ORDER BY cnt DESC LIMIT 5", conn)
    if not dupes.empty:
        print(dupes.to_string(index=False))
    else:
        print("No exact duplicates found.")

    conn.close()

if __name__ == "__main__":
    audit_database()
