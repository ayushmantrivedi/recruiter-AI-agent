#!/usr/bin/env python3
"""Fix leads table schema."""

import sys
sys.path.append('.')

from app.config import settings
from app.database import engine, Base, Lead
from sqlalchemy import text

print("=== FIXING LEADS TABLE SCHEMA ===")

try:
    with engine.connect() as conn:
        # Drop leads table
        print("Dropping leads table...")
        conn.execute(text("DROP TABLE IF EXISTS leads CASCADE"))
        conn.commit()

        # Recreate leads table
        print("Recreating leads table...")
        Lead.__table__.create(engine)

        # Verify schema
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'leads'
            ORDER BY ordinal_position
        """))

        print("leads table schema after fix:")
        for row in result:
            print(f"  {row[0]}: {row[1]} {'(nullable)' if row[2] == 'YES' else '(not null)'}")

        print("[OK] Leads table fixed")

except Exception as e:
    print(f"[ERROR] {e}")