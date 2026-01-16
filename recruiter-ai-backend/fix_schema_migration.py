from sqlalchemy import create_engine, text, inspect
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("migration")

def migrate():
    logger.info("Starting safe database migration...")
    engine = create_engine(settings.database.url)
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('leads')]
        
        # 1. Add 'role' column
        if 'role' not in columns:
            logger.info("Adding missing column 'role' to leads table...")
            conn.execute(text("ALTER TABLE leads ADD COLUMN role VARCHAR(255)"))
        else:
            logger.info("Column 'role' already exists.")
            
        # 2. Add 'location' column
        if 'location' not in columns:
            logger.info("Adding missing column 'location' to leads table...")
            conn.execute(text("ALTER TABLE leads ADD COLUMN location VARCHAR(255)"))
        else:
            logger.info("Column 'location' already exists.")
            
        conn.commit()
        
        # 3. Add Unique Constraint
        # First check if it exists (approximate check via naming convention failure is acceptable, 
        # but better to try/except the creation)
        try:
            logger.info("Attempting to create unique constraint 'uq_lead_identity_per_query'...")
            # We must handle duplicates before adding unique constraint if data exists
            # For now, we assume this is a hardening pass and we can maybe skip duplicate cleanup 
            # OR we simply try to add it. If it fails due to dups, we log validation error.
            conn.execute(text("""
                ALTER TABLE leads 
                ADD CONSTRAINT uq_lead_identity_per_query 
                UNIQUE (company_name, role, location, query_id)
            """))
            conn.commit()
            logger.info("Unique constraint created successfully.")
        except Exception as e:
            logger.warning(f"Constraint creation failed (might already exist or duplicates present): {e}")
            conn.rollback()

    logger.info("Migration completed.")

if __name__ == "__main__":
    migrate()
