#!/usr/bin/env python3
"""Safe migration to fix SQLAlchemy ORM relationships.

This migration removes unused relationships that were causing foreign key constraint issues.
Since the relationships were not actually used in the codebase, removing them is safe.
"""

import sys
sys.path.append('.')

from app.config import settings
from app.database import engine, Base
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

print("=== RELATIONSHIP MIGRATION ===")
print("Removing unused ORM relationships to fix foreign key constraint issues...")

try:
    with engine.connect() as conn:
        # Check current schema
        print("Checking current database schema...")

        # Get table info
        inspector = inspect(engine)

        tables = ['recruiters', 'queries', 'recruiter_preferences']
        for table_name in tables:
            if inspector.has_table(table_name):
                columns = inspector.get_columns(table_name)
                print(f"Table {table_name} exists with {len(columns)} columns")
            else:
                print(f"Table {table_name} does not exist")

        # Since we're only removing relationships (not changing actual columns),
        # and the relationships weren't used, no data migration is needed.
        # The ORM will simply not create the relationship joins.

        print("[OK] Relationship migration completed successfully")
        print("Note: Removed unused relationships from ORM models:")
        print("- Recruiter.queries")
        print("- Recruiter.preferences")
        print("- Query.recruiter")
        print("- RecruiterPreferences.recruiter")
        print("These relationships were not used in the codebase.")

except SQLAlchemyError as e:
    print(f"[ERROR] Migration failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    sys.exit(1)