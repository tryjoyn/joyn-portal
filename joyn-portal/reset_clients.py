"""
reset_clients.py — joyn-portal
One-shot script to clear all client data from the portal SQLite database.
Run this directly on Railway as a one-off command:
  railway run python reset_clients.py

Preserves: database schema, indexes, and all non-client tables.
Deletes (FK-safe order):
  password_reset_tokens → api_keys → outputs → activity_log → hired_staff → clients
"""
import sqlite3
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("DATABASE_PATH", "data/portal.db")

DELETION_ORDER = [
    "password_reset_tokens",
    "api_keys",
    "outputs",
    "activity_log",
    "hired_staff",
    "clients",
]


def reset_all_clients(db_path: str = DB_PATH):
    """Delete all client records from the portal SQLite database."""
    logger.info("Connecting to portal DB: %s", db_path)

    if not os.path.exists(db_path):
        logger.error("Database file not found: %s", db_path)
        return {"success": False, "error": f"DB not found: {db_path}"}

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    results = {}

    # Count before
    logger.info("── Counting records before deletion ──")
    for table in DELETION_ORDER:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info("  %s: %d rows", table, count)
            results[table] = {"before": count}
        except Exception as e:
            logger.warning("  %s: not found (%s)", table, e)
            results[table] = {"before": "N/A"}

    # Delete in FK-safe order
    logger.info("── Deleting all client records ──")
    try:
        with conn:
            for table in DELETION_ORDER:
                try:
                    conn.execute(f"DELETE FROM {table}")
                    logger.info("  ✓ Cleared %s", table)
                    results[table]["deleted"] = True
                except Exception as e:
                    logger.error("  ✗ Failed to clear %s: %s", table, e)
                    results[table]["error"] = str(e)
    except Exception as e:
        logger.error("Transaction failed: %s", e)
        conn.close()
        return {"success": False, "error": str(e)}

    # Verify
    logger.info("── Verifying empty state ──")
    all_clear = True
    for table in DELETION_ORDER:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            remaining = cursor.fetchone()[0]
            results[table]["after"] = remaining
            if remaining == 0:
                logger.info("  ✓ %s: EMPTY", table)
            else:
                logger.warning("  ✗ %s: %d rows remain", table, remaining)
                all_clear = False
        except Exception as e:
            logger.error("  %s: verification error: %s", table, e)

    conn.close()
    logger.info("Portal DB reset complete.")
    return {"success": all_clear, "tables": results}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DB_PATH
    result = reset_all_clients(path)
    if result["success"]:
        logger.info("✓ All client data successfully cleared.")
        sys.exit(0)
    else:
        logger.error("✗ Reset completed with errors.")
        sys.exit(1)
