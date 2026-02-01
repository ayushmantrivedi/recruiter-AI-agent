import sqlite3
import os

db_path = 'recruiter_ai.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE queries ADD COLUMN synthesis_report TEXT')
        conn.commit()
        print('Success: added synthesis_report column to queries table')
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e).lower():
            print('Note: synthesis_report column already exists')
        else:
            print(f'Error: {e}')
    finally:
        conn.close()
else:
    print(f'Error: {db_path} not found')
