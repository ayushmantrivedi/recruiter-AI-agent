import sqlite3

DB_PATH = "recruiter_ai.db"

def wipe_leads():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("Wiping all leads for a fresh Best-in-Class verification...")
    cursor.execute("DELETE FROM leads")
    conn.commit()
    print("Leads wiped.")
    conn.close()

if __name__ == "__main__":
    wipe_leads()
