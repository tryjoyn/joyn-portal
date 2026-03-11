-- Migration 003: Payment transactions table for Stripe
-- Run automatically by db.py _apply_migrations()
-- Tracks checkout sessions and payment status

CREATE TABLE IF NOT EXISTS payment_transactions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id       INTEGER REFERENCES clients(id),
    session_id      TEXT NOT NULL,
    amount          REAL NOT NULL,
    currency        TEXT DEFAULT 'usd',
    package_id      TEXT,
    status          TEXT DEFAULT 'pending',  -- pending | completed | failed | cancelled
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at    TIMESTAMP,
    metadata        TEXT  -- JSON blob for extra data
);

CREATE INDEX IF NOT EXISTS idx_payment_trans_client ON payment_transactions(client_id);
CREATE INDEX IF NOT EXISTS idx_payment_trans_session ON payment_transactions(session_id);
CREATE INDEX IF NOT EXISTS idx_payment_trans_status ON payment_transactions(status);
