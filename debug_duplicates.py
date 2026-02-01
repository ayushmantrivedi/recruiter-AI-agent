import sqlite3
import pandas as pd

DB_PATH = "recruiter_ai.db"

def inspect_specific_company():
    conn = sqlite3.connect(DB_PATH)
    try:
        # Get all columns for this specific company to verify diversity
        query = "SELECT id, company_name, role, location, score, created_at FROM leads WHERE company_name LIKE '%Humancapital%' ORDER BY id DESC"
        df = pd.read_sql_query(query, conn)
        print(f"--- Records for 'MY Humancapital GmbH' ({len(df)}) ---")
        if not df.empty:
            print(df.to_string())
        else:
            print("No records found. Maybe the clean_db script deleted them?")
    except Exception as e:
        print(e)
    finally:
        conn.close()

if __name__ == "__main__":
    inspect_specific_company()
