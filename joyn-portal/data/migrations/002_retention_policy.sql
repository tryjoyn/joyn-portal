-- Migration 002: Data retention policies
-- Run automatically by db.py _apply_migrations()
-- Adds retention_purged_at column and creates purge tracking table.

-- Track when bulletins/outputs were purged for compliance
CREATE TABLE IF NOT EXISTS retention_purge_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    purged_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    table_name      TEXT NOT NULL,
    records_purged  INTEGER DEFAULT 0,
    retention_days  INTEGER NOT NULL,
    notes           TEXT
);

-- Add index for outputs purge queries
CREATE INDEX IF NOT EXISTS idx_outputs_delivered_purge ON outputs(delivered_at);
CREATE INDEX IF NOT EXISTS idx_activity_timestamp_purge ON activity_log(timestamp);
