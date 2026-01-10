#!/usr/bin/env python3
"""Check database connection and schema."""

import sys
import os
sys.path.append('.')

try:
    from app.config import settings
    from app.database import engine, Base, Query, Recruiter, Lead
    from sqlalchemy import text, inspect
    from sqlalchemy.exc import SQLAlchemyError

    print("=== DATABASE CONNECTION TEST ===")

    # Test connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
        print("[OK] Database connection successful")
    except SQLAlchemyError as e:
        print(f"[ERROR] Database connection failed: {e}")
        sys.exit(1)

    # Check tables
    print("\n=== TABLE INSPECTION ===")
    inspector = inspect(engine)

    tables = inspector.get_table_names()
    print(f"Tables found: {tables}")

    if 'queries' in tables:
        print("[OK] queries table exists")

        # Get column info
        columns = inspector.get_columns('queries')
        print("\nqueries table schema:")
        for col in columns:
            print(f"  {col['name']}: {col['type']} {'(nullable)' if col['nullable'] else '(not null)'}")

        # Check sample data
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM queries")).scalar()
                print(f"\nqueries table has {result} rows")
        except Exception as e:
            print(f"Could not query table: {e}")

    else:
        print("[ERROR] queries table does not exist")

        # Try to create tables
        print("Attempting to create tables...")
        try:
            Base.metadata.create_all(bind=engine)
            print("[OK] Tables created successfully")

            # Clear inspector cache and re-inspect
            from sqlalchemy import inspect as sqlalchemy_inspect
            inspector = sqlalchemy_inspect(engine)
            tables = inspector.get_table_names()
            print(f"Tables after creation: {tables}")

            # Check queries table specifically
            if 'queries' in tables:
                print("[OK] queries table now exists")
                columns = inspector.get_columns('queries')
                print("\nqueries table schema:")
                for col in columns:
                    print(f"  {col['name']}: {col['type']} {'(nullable)' if col['nullable'] else '(not null)'}")
            else:
                print("[ERROR] queries table still missing")

        except Exception as e:
            print(f"[ERROR] Table creation failed: {e}")

except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")