"""
db.py — Transparent SQLite / PostgreSQL adapter for Joyn Builders API.

When DATABASE_URL is set (Railway Postgres), uses psycopg2 with %s placeholders.
When DB_PATH is set (local dev), uses sqlite3 with ? placeholders.

Usage:
    from db import get_db
    conn = get_db()
    rows = conn.execute("SELECT * FROM catalogue WHERE id=?", (role_id,)).fetchall()
    conn.close()

The adapter converts ? → %s automatically for Postgres, and wraps psycopg2
cursors to behave like sqlite3.Row (dict-like access by column name).
"""
import os
import re
import sqlite3

DATABASE_URL = os.environ.get("DATABASE_URL", "")
DB_PATH = os.environ.get("DB_PATH", "joyn_builders.db")

# Railway injects DATABASE_URL as postgres:// but psycopg2 needs postgresql://
def _fix_url(url):
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url

def _to_pg(sql):
    """Convert SQLite ? placeholders to PostgreSQL %s placeholders."""
    return sql.replace("?", "%s")

def _to_pg_ddl(sql):
    """
    Convert SQLite DDL to PostgreSQL DDL:
    - BOOLEAN DEFAULT FALSE/TRUE → kept as-is (Postgres supports it)
    - TEXT CHECK(...) → kept as-is (Postgres supports it)
    - executescript uses ; separator → split and run individually
    - AUTOINCREMENT → SERIAL (not used here)
    - Remove SQLite-specific pragmas
    """
    # Replace SQLite TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    # Postgres uses the same syntax, so no change needed.
    # Replace CREATE INDEX IF NOT EXISTS — Postgres supports this too.
    return sql


class _PgRow(dict):
    """Dict subclass that also supports integer index access like sqlite3.Row."""
    def __init__(self, cursor, row):
        cols = [d[0] for d in cursor.description]
        super().__init__(zip(cols, row))
        self._list = list(row)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._list[key]
        return super().__getitem__(key)

    def keys(self):
        return super().keys()


class _PgCursor:
    """Wraps psycopg2 cursor to behave like sqlite3 cursor with Row factory."""
    def __init__(self, cur):
        self._cur = cur
        self.description = None
        self.lastrowid = None

    def execute(self, sql, params=()):
        sql = _to_pg(sql)
        self._cur.execute(sql, params)
        self.description = self._cur.description
        return self

    def executemany(self, sql, seq):
        sql = _to_pg(sql)
        self._cur.executemany(sql, seq)
        return self

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        return _PgRow(self._cur, row)

    def fetchall(self):
        rows = self._cur.fetchall()
        return [_PgRow(self._cur, r) for r in rows]

    def __iter__(self):
        for row in self._cur:
            yield _PgRow(self._cur, row)

    def close(self):
        self._cur.close()


class _PgConn:
    """Wraps psycopg2 connection to behave like sqlite3 connection."""
    def __init__(self, conn):
        self._conn = conn
        self._cur = conn.cursor()

    def execute(self, sql, params=()):
        c = _PgCursor(self._conn.cursor())
        c.execute(sql, params)
        return c

    def executemany(self, sql, seq):
        c = _PgCursor(self._conn.cursor())
        c.executemany(sql, seq)
        return c

    def executescript(self, script):
        """Execute a multi-statement SQL script (SQLite-style)."""
        # Split on semicolons, skip empty statements
        statements = [s.strip() for s in script.split(";") if s.strip()]
        cur = self._conn.cursor()
        for stmt in statements:
            pg_stmt = _to_pg(_to_pg_ddl(stmt))
            try:
                cur.execute(pg_stmt)
            except Exception as e:
                # Ignore "already exists" errors for CREATE TABLE/INDEX
                msg = str(e).lower()
                if "already exists" in msg or "duplicate" in msg:
                    self._conn.rollback()
                else:
                    self._conn.rollback()
                    raise
        cur.close()
        return self

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


def get_db():
    """Return a database connection (SQLite or PostgreSQL) with a unified API."""
    if DATABASE_URL:
        try:
            import psycopg2
        except ImportError:
            raise RuntimeError(
                "psycopg2 is required for PostgreSQL. Add psycopg2-binary to requirements.txt"
            )
        conn = psycopg2.connect(_fix_url(DATABASE_URL))
        conn.autocommit = False
        return _PgConn(conn)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
