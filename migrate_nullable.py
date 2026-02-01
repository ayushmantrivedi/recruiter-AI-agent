#!/usr/bin/env python3
"""Migrate database to make recruiter_id nullable."""

import sys
sys.path.append('.')

from app.config import settings
from app.database import engine, Base, Query, Recruiter, Lead
from sqlalchemy import text

print("=== MIGRATING recruiter_id TO NULLABLE ===")

try:
    with engine.connect() as conn:
        # Drop and recreate queries table with new schema
        print("Recreating queries table...")
        conn.execute(text("DROP TABLE IF EXISTS queries CASCADE"))
        conn.commit()

        # Recreate all tables
        Base.metadata.create_all(bind=engine)

        print("[OK] Migration completed")

except Exception as e:
    print(f"[ERROR] Migration failed: {e}")
    sys.exit(1)