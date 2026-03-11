-- Migration 001: LLM usage and cost tracking
-- Run automatically by db.py _apply_migrations()
-- Tracks every Claude API call for cost attribution per client and workflow.

CREATE TABLE IF NOT EXISTS llm_usage (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Attribution
    client_id       INTEGER REFERENCES clients(id),   -- NULL = system-level call (e.g. build bot)
    staff_slug      TEXT,                              -- 'iris', 'probe', etc.
    workflow        TEXT,                              -- e.g. 'bulletin_analysis', 'impact_assessment'
    trace_id        TEXT,                              -- links to observability span

    -- Model
    model           TEXT NOT NULL,                    -- e.g. 'claude-opus-4-6'
    provider        TEXT DEFAULT 'anthropic',

    -- Token counts (from API response usage object)
    input_tokens    INTEGER DEFAULT 0,
    output_tokens   INTEGER DEFAULT 0,
    cache_read_tokens   INTEGER DEFAULT 0,
    cache_write_tokens  INTEGER DEFAULT 0,

    -- Cost in USD (calculated at call time using known pricing)
    cost_usd        REAL DEFAULT 0.0,

    -- Outcome
    status          TEXT DEFAULT 'success',           -- 'success' | 'error' | 'timeout'
    latency_ms      INTEGER,
    error_message   TEXT
);

CREATE INDEX IF NOT EXISTS idx_llm_usage_client     ON llm_usage(client_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_recorded   ON llm_usage(recorded_at);
CREATE INDEX IF NOT EXISTS idx_llm_usage_staff      ON llm_usage(staff_slug);
CREATE INDEX IF NOT EXISTS idx_llm_usage_trace      ON llm_usage(trace_id);
