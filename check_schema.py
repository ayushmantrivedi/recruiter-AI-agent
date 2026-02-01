#!/usr/bin/env python3
"""Check database schema."""

from app.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)

print("=== QUERIES TABLE SCHEMA ===")
columns = inspector.get_columns('queries')
for col in columns:
    print(f"{col['name']}: {col['type']} (nullable: {col.get('nullable', True)})")

print("\n=== FOREIGN KEYS ===")
fks = inspector.get_foreign_keys('queries')
for fk in fks:
    print(f"  {fk}")

print("\n=== INDEXES ===")
indexes = inspector.get_indexes('queries')
for idx in indexes:
    print(f"  {idx['name']}: {idx['column_names']}")