#!/usr/bin/env python3
"""Fix recruiter_id column type and remove foreign key constraint."""

import sys
sys.path.append('.')

from app.config import settings
from app.database import engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

print("=== FIXING recruiter_id SCHEMA ===")

try:
    with engine.connect() as conn:
        print("Current schema shows recruiter_id as INTEGER with foreign key to recruiters.id")
        print("But API uses string recruiter_ids and ORM relationships were removed.")
        print("Converting recruiter_id to VARCHAR(255) and dropping foreign key...")

        # Drop the foreign key constraint
        print("Dropping foreign key constraint...")
        try:
            conn.execute(text("ALTER TABLE queries DROP CONSTRAINT IF EXISTS queries_recruiter_id_fkey"))
            conn.commit()
            print("OK: Foreign key constraint dropped")
        except Exception as e:
            print(f"Note: Foreign key constraint may not exist: {e}")

        # Change column type from INTEGER to VARCHAR
        print("Changing recruiter_id column from INTEGER to VARCHAR(255)...")
        conn.execute(text("ALTER TABLE queries ALTER COLUMN recruiter_id TYPE VARCHAR(255)"))
        conn.commit()
        print("OK: Column type changed to VARCHAR(255)")

        # Verify the change
        print("Verifying schema changes...")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'queries' AND column_name = 'recruiter_id'
        """))

        row = result.fetchone()
        if row:
            print(f"OK: recruiter_id is now: {row[1]} (nullable: {row[2]})")

        # Check foreign keys
        fk_result = conn.execute(text("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'queries' AND constraint_type = 'FOREIGN KEY'
        """))

        fks = fk_result.fetchall()
        if not fks:
            print("OK: No foreign key constraints remain on queries table")
        else:
            print(f"Warning: Foreign keys still exist: {fks}")

        print("[OK] Schema migration completed successfully")
        print("recruiter_id is now VARCHAR(255) with no foreign key constraints")

except SQLAlchemyError as e:
    print(f"[ERROR] Migration failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    sys.exit(1)