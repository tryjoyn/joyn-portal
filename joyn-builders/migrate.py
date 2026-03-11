"""
Database migration script — run before starting the app on Railway.
Safely adds new columns to existing databases without data loss.
Supports both SQLite (local) and PostgreSQL (Railway).
"""
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "")
DB_PATH = os.environ.get("DB_PATH", "joyn_builders.db")

MIGRATIONS = [
    # v1.1 — Founding Builder and revenue share fields
    ("ALTER TABLE builders ADD COLUMN is_founding_builder BOOLEAN DEFAULT FALSE", "is_founding_builder"),
    ("ALTER TABLE builders ADD COLUMN revenue_share REAL DEFAULT 0.70", "revenue_share"),
    # v1.2 — Catalogue builder_count tracking
    ("ALTER TABLE catalogue ADD COLUMN builder_count INTEGER DEFAULT 0", "catalogue.builder_count"),
]

def run_migrations():
    if DATABASE_URL:
        _run_pg()
    else:
        _run_sqlite()

def _run_pg():
    try:
        import psycopg2
        import psycopg2.errors
    except ImportError:
        print("[MIGRATE] psycopg2 not available, skipping Postgres migration")
        return

    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    conn = psycopg2.connect(url)
    conn.autocommit = False
    cur = conn.cursor()

    for sql, col_name in MIGRATIONS:
        try:
            cur.execute(sql)
            conn.commit()
            print(f"[MIGRATE] Added column: {col_name}")
        except Exception as e:
            conn.rollback()
            msg = str(e).lower()
            if "already exists" in msg or "duplicate" in msg:
                print(f"[MIGRATE] Column already exists: {col_name}")
            else:
                print(f"[MIGRATE] Error on {col_name}: {e}")

    cur.close()
    conn.close()
    print("[MIGRATE] Done (Postgres).")

def _run_sqlite():
    import sqlite3
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
    print("[MIGRATE] Done (SQLite).")

if __name__ == "__main__":
    run_migrations()
