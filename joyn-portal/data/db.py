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
    """
    Apply all incremental migrations in order.  Every statement is wrapped in
    a try/except so it is safe to re-run on an existing database.

    Convention: add new ALTER TABLE / CREATE TABLE statements here when
    introducing schema changes after the initial deploy.  For larger changes,
    add a SQL file to data/migrations/ and load it via _apply_migration_files().
    """
    inline_migrations = [
        # Original column additions
        "ALTER TABLE clients ADD COLUMN states TEXT",
        "ALTER TABLE clients ADD COLUMN first_login INTEGER DEFAULT 0",
    ]
    for sql in inline_migrations:
        try:
            db.execute(sql)
        except Exception:
            pass  # Column already exists — ignore

    _apply_migration_files(db)
    db.commit()


def _apply_migration_files(db):
    """
    Execute all *.sql files in data/migrations/ in filename order.
    Each file is executed as a script (supports multiple statements).
    Safe to re-run because every migration file uses CREATE TABLE IF NOT EXISTS
    and CREATE INDEX IF NOT EXISTS.
    """
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    if not os.path.isdir(migrations_dir):
        return

    sql_files = sorted(
        f for f in os.listdir(migrations_dir) if f.endswith('.sql')
    )
    for filename in sql_files:
        path = os.path.join(migrations_dir, filename)
        try:
            with open(path) as f:
                db.executescript(f.read())
        except Exception as exc:
            # Log but do not crash — allows partial migrations on existing DBs
            import logging
            logging.getLogger(__name__).warning(
                'Migration file %s skipped: %s', filename, exc
            )


def init_db():
    db = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path) as f:
        db.executescript(f.read())
    _apply_migrations(db)
    db.commit()
    _seed_default_user(db)


def _seed_default_user(db):
    """Create default admin user if no users exist."""
    import bcrypt
    
    # Check if any users exist
    result = db.execute('SELECT COUNT(*) as c FROM clients').fetchone()
    if result['c'] > 0:
        return  # Users already exist
    
    # Create default user: itsshiva@outlook.com / Dmwmp@2615
    password_hash = bcrypt.hashpw('Dmwmp@2615'.encode(), bcrypt.gensalt(rounds=12)).decode()
    db.execute(
        '''INSERT INTO clients (email, password_hash, company_name, subscription_status)
           VALUES (?, ?, ?, ?)''',
        ('itsshiva@outlook.com', password_hash, 'Joyn', 'active')
    )
    db.commit()
    import logging
    logging.getLogger(__name__).info('Default user created: itsshiva@outlook.com')


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
