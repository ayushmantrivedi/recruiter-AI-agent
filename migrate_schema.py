
import sys
import os
from sqlalchemy import text

sys.path.append(os.getcwd())

from app.database import engine, SessionLocal

def migrate_db():
    print("Migrating database schema...")
    with engine.connect() as conn:
        # Check if version is sqlite or something else
        # Simple generic ALTER TABLE, handling failure if exists
        
        # Add intelligence column
        try:
            conn.execute(text("ALTER TABLE queries ADD COLUMN intelligence JSON"))
            print("Added intelligence column.")
        except Exception as e:
            print(f"Intelligence column might already exist or error: {e}")
            
        # Add signals column
        try:
            conn.execute(text("ALTER TABLE queries ADD COLUMN signals JSON"))
            print("Added signals column.")
        except Exception as e:
            print(f"Signals column might already exist or error: {e}")
            
        conn.commit()
    print("Migration complete.")

if __name__ == "__main__":
    migrate_db()
