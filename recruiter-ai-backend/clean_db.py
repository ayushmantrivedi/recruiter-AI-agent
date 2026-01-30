import sqlite3
import pandas as pd

DB_PATH = "recruiter_ai.db"

def clean_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Count before
    cursor.execute("SELECT COUNT(*) FROM leads WHERE role IS NULL")
    bad_leads = cursor.fetchone()[0]
    print(f"Found {bad_leads} leads with NULL role.")
    
    if bad_leads > 0:
        print("Deleting corrupted leads...")
        cursor.execute("DELETE FROM leads WHERE role IS NULL")
        conn.commit()
        print(f"Deleted {bad_leads} leads.")
        
    conn.close()

if __name__ == "__main__":
    clean_database()
