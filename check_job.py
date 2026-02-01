#!/usr/bin/env python3
"""Check if job was created in database."""

import sys
sys.path.append('.')

from app.config import settings
from app.database import engine, Query
from sqlalchemy import text

print("=== CHECKING JOB IN DATABASE ===")

try:
    with engine.connect() as conn:
        # Check total queries
        result = conn.execute(text("SELECT COUNT(*) FROM queries")).scalar()
        print(f"Total queries in database: {result}")

        if result > 0:
            # Get all queries
            result = conn.execute(text("SELECT id, query_text, processing_status, created_at FROM queries ORDER BY created_at DESC"))
            rows = result.fetchall()
            for i, row in enumerate(rows):
                print(f"Query {i+1}: ID={row[0]}, Status={row[2]}, Query='{row[1]}'")

except Exception as e:
    print(f"[ERROR] {e}")