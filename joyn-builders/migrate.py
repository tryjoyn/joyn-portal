"""
Database migration script — run before starting the app on Railway.
Safely adds new columns to existing databases without data loss.
"""
import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "joyn_builders.db")

MIGRATIONS = [
    # v1.1 — Founding Builder and revenue share fields
    ("ALTER TABLE builders ADD COLUMN is_founding_builder BOOLEAN DEFAULT FALSE", "is_founding_builder"),
    ("ALTER TABLE builders ADD COLUMN revenue_share REAL DEFAULT 0.70", "revenue_share"),
    # v1.2 — Catalogue builder_count tracking
    ("ALTER TABLE catalogue ADD COLUMN builder_count INTEGER DEFAULT 0", "catalogue.builder_count"),
]

def run_migrations():
    conn = sqlite3.connect(DB_PATH)
    for sql, col_name in MIGRATIONS:
        try:
            conn.execute(sql)
            conn.commit()
            print(f"[MIGRATE] Added column: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"[MIGRATE] Column already exists: {col_name}")
            else:
                print(f"[MIGRATE] Error on {col_name}: {e}")
    conn.close()
    print("[MIGRATE] Done.")

if __name__ == "__main__":
    run_migrations()
