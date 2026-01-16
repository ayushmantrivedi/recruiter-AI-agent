from app.database import create_tables, engine, Base, ExecutionReport
from app.utils.logger import setup_logging

if __name__ == "__main__":
    setup_logging()
    print("Updating database schema...")
    # This will create any tables that don't exist
    # It will NOT update existing tables (no migration tool), but we added a NEW table.
    create_tables()
    print("Schema update complete.")
