#!/usr/bin/env python3
"""Migrate database schema to fix Query.id type."""

import sys
sys.path.append('.')

from app.config import settings
from app.database import engine, Base, Query, Recruiter, Lead
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

print("=== DATABASE MIGRATION ===")

try:
    with engine.connect() as conn:
        # Drop existing queries table if it exists
        print("Dropping existing queries table...")
        conn.execute(text("DROP TABLE IF EXISTS queries CASCADE"))
        conn.commit()

        # Recreate all tables
        print("Recreating tables...")
        Base.metadata.create_all(bind=engine)

        # Verify schema
        print("Verifying queries table schema...")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'queries'
            ORDER BY ordinal_position
        """))

        print("queries table schema:")
        for row in result:
            print(f"  {row[0]}: {row[1]} ({'nullable' if row[2] == 'YES' else 'not null'})")

        print("[OK] Migration completed successfully")

except SQLAlchemyError as e:
    print(f"[ERROR] Migration failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    sys.exit(1)