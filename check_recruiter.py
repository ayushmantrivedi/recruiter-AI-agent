#!/usr/bin/env python3
"""Check if recruiter with ID 2 exists."""

import sys
sys.path.append('.')

from app.config import settings
from app.database import engine, Recruiter
from sqlalchemy import text

print("=== CHECKING RECRUITER ID 2 ===")

try:
    with engine.connect() as conn:
        # Check if recruiter with ID 2 exists
        result = conn.execute(text("SELECT id, email, is_active FROM recruiters WHERE id = 2"))
        row = result.fetchone()

        if row:
            print(f"[OK] Recruiter found: ID={row[0]}, Email={row[1]}, Active={row[2]}")
        else:
            print("[ERROR] Recruiter with ID 2 not found")

            # Check if any recruiters exist
            result = conn.execute(text("SELECT COUNT(*) FROM recruiters"))
            count = result.scalar()
            print(f"Total recruiters in database: {count}")

            if count == 0:
                print("Creating test recruiter...")
                # Create a test recruiter
                conn.execute(text("""
                    INSERT INTO recruiters (id, email, hashed_password, full_name, is_active, created_at)
                    VALUES (2, 'test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj7UeCwZkLW', 'Test Recruiter', true, NOW())
                """))
                conn.commit()
                print("[OK] Test recruiter created with ID=2")

except Exception as e:
    print(f"[ERROR] {e}")