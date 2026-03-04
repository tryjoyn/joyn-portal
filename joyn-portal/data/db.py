import sqlite3
import os
from flask import g, current_app


def get_db():
    if 'db' not in g:
        db_path = current_app.config.get('DATABASE_PATH', 'data/portal.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA journal_mode=WAL')
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def _apply_migrations(db):
    """Add columns introduced after initial schema deploy. Safe to re-run."""
    migrations = [
        "ALTER TABLE clients ADD COLUMN states TEXT",
        "ALTER TABLE clients ADD COLUMN first_login INTEGER DEFAULT 0",
    ]
    for sql in migrations:
        try:
            db.execute(sql)
        except Exception:
            pass  # Column already exists — ignore
    db.commit()


def init_db():
    db = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path) as f:
        db.executescript(f.read())
    _apply_migrations(db)
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)


# ── Query helpers ──────────────────────────────────────────────

def query(sql, params=()):
    return get_db().execute(sql, params).fetchall()


def query_one(sql, params=()):
    return get_db().execute(sql, params).fetchone()


def execute(sql, params=()):
    get_db().execute(sql, params)


def execute_commit(sql, params=()):
    db = get_db()
    db.execute(sql, params)
    db.commit()


def insert(sql, params=()):
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    return cur.lastrowid


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    return [dict(r) for r in rows]
