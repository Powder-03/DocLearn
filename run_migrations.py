#!/usr/bin/env python3
"""
Standalone script to run database migrations.

This should be run manually or as a Cloud Run Job before deploying new versions.

Usage:
    python run_migrations.py
"""
import sys
import logging

from app.db.session import run_migrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


def main():
    """Run database migrations."""
    try:
        log.info("Starting database migrations...")
        run_migrations()
        log.info("✓ Migrations completed successfully")
        return 0
    except Exception as e:
        log.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
