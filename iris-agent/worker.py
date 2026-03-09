"""
iris-agent/worker.py
─────────────────────
Event-driven worker that polls a SQLite queue and dispatches jobs to the
SupervisorAgent.

Queue design (SQLite `queue_jobs` table):
  - status: 'pending' → 'processing' → 'complete' | 'failed'
  - Atomic claiming via UPDATE ... WHERE status='pending' LIMIT 1
  - Exponential backoff on consecutive failures (max 5 retries per job)
  - Graceful SIGTERM / SIGINT shutdown — finishes current job before exiting

Environment variables:
  IRIS_DB_PATH         Path to SQLite database (default: data/iris.db)
  IRIS_POLL_INTERVAL   Seconds between queue polls (default: 30)
  IRIS_MODEL           Anthropic model to use (default: claude-haiku-3-5)
  JOYN_PORTAL_URL      Portal base URL for tool API calls
  JOYN_PORTAL_SECRET   Shared secret for portal authentication
  ANTHROPIC_API_KEY    Anthropic API key
"""

from __future__ import annotations

import json
import logging
import os
import signal
import sqlite3
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("iris.worker")

DB_PATH       = os.environ.get("IRIS_DB_PATH", "data/iris.db")
POLL_INTERVAL = int(os.environ.get("IRIS_POLL_INTERVAL", "30"))
MAX_RETRIES   = 5


# ── Database helpers ───────────────────────────────────────────────────────────

@contextmanager
def get_db():
    """Yield a SQLite connection with WAL mode and row factory."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create the queue_jobs table if it does not exist."""
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS queue_jobs (
                id           TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                job_type     TEXT NOT NULL DEFAULT 'bulletin_analysis',
                client_id    INTEGER NOT NULL,
                payload      TEXT NOT NULL,          -- JSON
                status       TEXT NOT NULL DEFAULT 'pending'
                                 CHECK(status IN ('pending','processing','complete','failed')),
                priority     INTEGER NOT NULL DEFAULT 5,  -- 1=highest, 10=lowest
                retry_count  INTEGER NOT NULL DEFAULT 0,
                error_msg    TEXT,
                trace_id     TEXT,
                created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
                claimed_at   TEXT,
                completed_at TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_queue_status_priority
            ON queue_jobs(status, priority, created_at)
        """)
    logger.info("Queue DB initialised at %s", DB_PATH)


def claim_next_job() -> Optional[sqlite3.Row]:
    """
    Atomically claim the next pending job.
    Returns the job row or None if the queue is empty.
    """
    with get_db() as conn:
        row = conn.execute("""
            SELECT id FROM queue_jobs
            WHERE status = 'pending'
              AND retry_count < ?
            ORDER BY priority ASC, created_at ASC
            LIMIT 1
        """, (MAX_RETRIES,)).fetchone()

        if row is None:
            return None

        job_id = row["id"]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        conn.execute("""
            UPDATE queue_jobs
            SET status = 'processing', claimed_at = ?
            WHERE id = ? AND status = 'pending'
        """, (now, job_id))

        return conn.execute(
            "SELECT * FROM queue_jobs WHERE id = ?", (job_id,)
        ).fetchone()


def complete_job(job_id: str, trace_id: Optional[str] = None):
    """Mark a job as complete."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with get_db() as conn:
        conn.execute("""
            UPDATE queue_jobs
            SET status = 'complete', completed_at = ?, trace_id = ?
            WHERE id = ?
        """, (now, trace_id, job_id))


def fail_job(job_id: str, error_msg: str):
    """
    Increment retry count. If max retries reached, mark as failed.
    Otherwise return to 'pending' for retry.
    """
    with get_db() as conn:
        row = conn.execute(
            "SELECT retry_count FROM queue_jobs WHERE id = ?", (job_id,)
        ).fetchone()

        if row is None:
            return

        new_count = (row["retry_count"] or 0) + 1
        new_status = "failed" if new_count >= MAX_RETRIES else "pending"

        conn.execute("""
            UPDATE queue_jobs
            SET status = ?, retry_count = ?, error_msg = ?, claimed_at = NULL
            WHERE id = ?
        """, (new_status, new_count, error_msg[:2000], job_id))

        logger.warning(
            "Job %s → %s (attempt %d/%d): %s",
            job_id, new_status, new_count, MAX_RETRIES, error_msg[:200]
        )


# ── Job helpers ────────────────────────────────────────────────────────────────

def enqueue_bulletin_job(client_id: int, bulletins: list, priority: int = 5) -> str:
    """
    Add a bulletin analysis job to the queue.
    Returns the new job ID.
    """
    job_id = str(uuid.uuid4()).replace("-", "")
    payload = json.dumps({"client_id": client_id, "bulletins": bulletins})
    with get_db() as conn:
        conn.execute("""
            INSERT INTO queue_jobs (id, job_type, client_id, payload, priority)
            VALUES (?, 'bulletin_analysis', ?, ?, ?)
        """, (job_id, client_id, payload, priority))
    logger.info("Enqueued bulletin job %s for client %s (%d bulletins)", job_id, client_id, len(bulletins))
    return job_id


# ── Worker loop ────────────────────────────────────────────────────────────────

class IrisWorker:
    """
    Polls the SQLite queue and dispatches jobs to the SupervisorAgent.

    Shutdown: send SIGTERM or SIGINT. The worker finishes the current job
    before exiting cleanly.
    """

    def __init__(self):
        self._running = False
        self._shutdown_requested = False

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT,  self._handle_signal)

    def _handle_signal(self, signum, frame):
        sig_name = signal.Signals(signum).name
        logger.info("Received %s — finishing current job then shutting down", sig_name)
        self._shutdown_requested = True

    def start(self):
        """Start the polling loop. Blocks until shutdown."""
        logger.info(
            "Iris worker starting | db=%s poll_interval=%ds",
            DB_PATH, POLL_INTERVAL
        )
        init_db()

        # Lazy import — only needed at runtime, not at import time
        from agents.supervisor import SupervisorAgent
        supervisor = SupervisorAgent()

        self._running = True
        consecutive_empty = 0

        while self._running and not self._shutdown_requested:
            job = claim_next_job()

            if job is None:
                consecutive_empty += 1
                # Exponential backoff up to 5 minutes when queue is empty
                sleep_time = min(POLL_INTERVAL * (2 ** min(consecutive_empty - 1, 4)), 300)
                logger.debug("Queue empty — sleeping %ds", sleep_time)
                self._interruptible_sleep(sleep_time)
                continue

            consecutive_empty = 0
            self._process_job(supervisor, job)

        logger.info("Iris worker shut down cleanly")

    def _process_job(self, supervisor, job):
        """Process a single job row."""
        job_id    = job["id"]
        client_id = job["client_id"]

        logger.info(
            "Processing job %s | client=%s type=%s",
            job_id, client_id, job["job_type"]
        )

        try:
            payload = json.loads(job["payload"])
        except json.JSONDecodeError as exc:
            fail_job(job_id, f"Invalid JSON payload: {exc}")
            return

        try:
            result = supervisor.run(payload)

            if result.get("status") == "error":
                fail_job(job_id, result.get("error", "Unknown error"))
            else:
                complete_job(job_id, trace_id=result.get("trace_id"))
                logger.info(
                    "Job %s complete | client=%s tools=%d summary=%s",
                    job_id, client_id,
                    result.get("tool_calls", 0),
                    result.get("summary", "")[:120],
                )

        except Exception as exc:
            logger.error("Job %s raised exception: %s", job_id, exc, exc_info=True)
            fail_job(job_id, str(exc))

    def _interruptible_sleep(self, seconds: float):
        """Sleep in 1-second increments so SIGTERM is handled promptly."""
        elapsed = 0.0
        while elapsed < seconds and not self._shutdown_requested:
            time.sleep(min(1.0, seconds - elapsed))
            elapsed += 1.0


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Quick smoke-test: enqueue a sample job and process it
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("Running smoke test...")
        init_db()
        sample_bulletins = [
            {
                "id": "test-001",
                "title": "Florida OIR Bulletin 2025-01: Homeowners Rate Filing Requirements",
                "state": "FL",
                "source": "Florida OIR",
                "published_at": "2025-01-15",
                "content": (
                    "The Florida Office of Insurance Regulation hereby issues guidance "
                    "on updated homeowners insurance rate filing requirements effective "
                    "March 1, 2025. All insurers writing homeowners coverage in Florida "
                    "must submit revised rate filings demonstrating compliance with the "
                    "new actuarial standards by February 15, 2025."
                ),
                "url": "https://www.floir.com/bulletins/2025-01"
            }
        ]
        job_id = enqueue_bulletin_job(client_id=1, bulletins=sample_bulletins, priority=1)
        logger.info("Enqueued test job: %s", job_id)

        from agents.supervisor import SupervisorAgent
        supervisor = SupervisorAgent()
        job = claim_next_job()
        if job:
            payload = json.loads(job["payload"])
            result = supervisor.run(payload)
            if result.get("status") == "error":
                fail_job(job["id"], result.get("error", ""))
                logger.error("Smoke test FAILED: %s", result.get("error"))
                sys.exit(1)
            else:
                complete_job(job["id"], trace_id=result.get("trace_id"))
                logger.info("Smoke test PASSED: %s", result.get("summary", ""))
                sys.exit(0)
        else:
            logger.error("Smoke test FAILED: could not claim job")
            sys.exit(1)

    # Normal operation
    worker = IrisWorker()
    worker.start()
