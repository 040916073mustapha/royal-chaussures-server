"""
RC Agents — Database Migration Script
Creates all tables on the target PostgreSQL database (or SQLite for local dev)

Usage:
    python migrate.py                          # Uses DATABASE_URL from env
    python migrate.py postgresql://user:pass@host/db   # Explicit URL
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migrate")

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Base, get_engine


def main():
    # Read database URL from argument or environment
    db_url = sys.argv[1] if len(sys.argv) > 1 else (
        os.getenv("SAAS_DATABASE_URL") or os.getenv("DATABASE_URL")
    )

    if not db_url:
        logger.error("No DATABASE_URL found. Set DATABASE_URL or SAAS_DATABASE_URL env var.")
        sys.exit(1)

    # Mask password in log
    safe_url = db_url.split("@")[-1] if "@" in db_url else db_url
    logger.info(f"Connecting to database at ...{safe_url[:60]}")

    engine = get_engine(db_url)

    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute("SELECT version()" if "postgres" in db_url else "SELECT 1")
            logger.info(f"Connected successfully: {result.fetchone()[0][:80] if 'postgres' in db_url else 'SQLite'}")

        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("✅ All tables created successfully!")

        # List tables
        if "postgres" in db_url:
            inspector = __import__("sqlalchemy").inspect(engine)
        else:
            inspector = __import__("sqlalchemy").inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Tables: {', '.join(tables)}")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
