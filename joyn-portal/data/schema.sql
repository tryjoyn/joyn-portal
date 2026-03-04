-- Joyn Client Portal — SQLite Schema
-- Run via: flask init-db  (auto-runs on first startup)
-- NEVER drop existing tables.

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS clients (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    email                   TEXT UNIQUE NOT NULL,
    password_hash           TEXT NOT NULL,
    company_name            TEXT NOT NULL,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login              TIMESTAMP,
    stripe_customer_id      TEXT,
    stripe_subscription_id  TEXT,
    subscription_status     TEXT DEFAULT 'trial',
    trial_ends_at           TIMESTAMP,
    -- profile extras
    business_reg_no         TEXT,
    industry                TEXT,
    address                 TEXT,
    website                 TEXT,
    team_size               TEXT,
    primary_contact_name    TEXT,
    primary_contact_phone   TEXT,
    briefing_emails         TEXT   -- comma-separated
);

CREATE TABLE IF NOT EXISTS hired_staff (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id   INTEGER NOT NULL REFERENCES clients(id),
    staff_name  TEXT NOT NULL,
    staff_slug  TEXT NOT NULL,
    hired_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status      TEXT DEFAULT 'active',   -- active | paused | let-go
    vertical    TEXT,
    mode        TEXT,
    settings    TEXT DEFAULT '{}'        -- JSON blob for staff-specific settings
);

CREATE TABLE IF NOT EXISTS activity_log (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id           INTEGER NOT NULL REFERENCES clients(id),
    staff_name          TEXT NOT NULL,
    staff_slug          TEXT NOT NULL,
    timestamp           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_type         TEXT,
    action_description  TEXT NOT NULL,
    status              TEXT DEFAULT 'complete'
);

CREATE TABLE IF NOT EXISTS outputs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id    INTEGER NOT NULL REFERENCES clients(id),
    staff_name   TEXT NOT NULL,
    staff_slug   TEXT NOT NULL,
    delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    output_type  TEXT,
    title        TEXT NOT NULL,
    summary      TEXT,
    severity     TEXT,   -- critical | high | medium | low | info
    full_content TEXT,
    read_at      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id   INTEGER NOT NULL REFERENCES clients(id),
    token_hash  TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at  TIMESTAMP NOT NULL,
    used_at     TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_keys (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash    TEXT NOT NULL,
    description TEXT,
    scope       TEXT DEFAULT 'log',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used   TIMESTAMP,
    revoked_at  TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_hired_staff_client    ON hired_staff(client_id);
CREATE INDEX IF NOT EXISTS idx_hired_staff_slug      ON hired_staff(staff_slug);
CREATE INDEX IF NOT EXISTS idx_activity_client       ON activity_log(client_id);
CREATE INDEX IF NOT EXISTS idx_activity_timestamp    ON activity_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_slug         ON activity_log(staff_slug);
CREATE INDEX IF NOT EXISTS idx_outputs_client        ON outputs(client_id);
CREATE INDEX IF NOT EXISTS idx_outputs_slug          ON outputs(staff_slug);
CREATE INDEX IF NOT EXISTS idx_outputs_delivered     ON outputs(delivered_at);
CREATE INDEX IF NOT EXISTS idx_reset_tokens_hash     ON password_reset_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash         ON api_keys(key_hash);
