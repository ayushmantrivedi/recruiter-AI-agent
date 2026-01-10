#!/usr/bin/env python3
"""Check actual database schema."""

import sys
sys.path.append('.')

from app.config import settings
from app.database import engine

print("=== CHECKING ACTUAL DATABASE SCHEMA ===")

try:
    with engine.connect() as conn:
        # Check leads table schema
        from sqlalchemy import text
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'leads'
            ORDER BY ordinal_position
        """))

        print("leads table schema:")
        for row in result:
            print(f"  {row[0]}: {row[1]} {'(nullable)' if row[2] == 'YES' else '(not null)'}")

except Exception as e:
    print(f"[ERROR] {e}")