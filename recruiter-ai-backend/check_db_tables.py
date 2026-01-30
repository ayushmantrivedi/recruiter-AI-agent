import sqlite3

DB_PATH = "recruiter.db"

def list_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in DB:", tables)
    conn.close()

if __name__ == "__main__":
    list_tables()
