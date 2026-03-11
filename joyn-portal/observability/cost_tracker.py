"""
observability/cost_tracker.py
─────────────────────────────
Wraps every Anthropic Claude API call to record token usage and estimated
cost in the `llm_usage` table.  Drop-in replacement for direct
`client.messages.create(...)` calls throughout the codebase.

Usage
-----
    from observability.cost_tracker import tracked_completion

    response = tracked_completion(
        client=anthropic_client,
        model="claude-opus-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": "..."}],
        system="...",
        # attribution (all optional — pass what you know)
        client_id=42,
        staff_slug="iris",
        workflow="bulletin_analysis",
        trace_id="abc-123",
    )
    # response is the normal Anthropic Message object — no API changes needed.

Cost model (USD per 1M tokens, as of March 2026)
-------------------------------------------------
These are approximate list prices.  Update PRICING_TABLE when Anthropic
changes rates.  The tracker is intentionally conservative — it rounds up.
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Pricing table (USD per 1M tokens) ─────────────────────────────────────────
# Source: https://www.anthropic.com/pricing  (updated March 2026)
PRICING_TABLE: dict[str, dict[str, float]] = {
    "claude-opus-4-6": {
        "input":        15.00,
        "output":       75.00,
        "cache_read":    1.50,
        "cache_write":  18.75,
    },
    "claude-sonnet-4-5": {
        "input":         3.00,
        "output":       15.00,
        "cache_read":    0.30,
        "cache_write":   3.75,
    },
    "claude-haiku-3-5": {
        "input":         0.80,
        "output":        4.00,
        "cache_read":    0.08,
        "cache_write":   1.00,
    },
    # Fallback for unknown models — use Opus pricing (conservative)
    "_default": {
        "input":        15.00,
        "output":       75.00,
        "cache_read":    1.50,
        "cache_write":  18.75,
    },
}

# Hard budget limit per single call (USD).  Raises CostBudgetExceeded if
# the *estimated* cost (based on max_tokens) would exceed this.
SINGLE_CALL_BUDGET_USD: float = 5.00

# Hard budget limit per client per rolling 24-hour window (USD).
# Enforced in tracked_completion() via _check_daily_budget().
DAILY_CLIENT_BUDGET_USD: float = 50.00


class CostBudgetExceeded(Exception):
    """Raised when a call would exceed a configured cost budget."""


def _calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> float:
    """Return estimated cost in USD for a completed API call."""
    pricing = PRICING_TABLE.get(model, PRICING_TABLE["_default"])
    cost = (
        (input_tokens        / 1_000_000) * pricing["input"]
        + (output_tokens       / 1_000_000) * pricing["output"]
        + (cache_read_tokens   / 1_000_000) * pricing["cache_read"]
        + (cache_write_tokens  / 1_000_000) * pricing["cache_write"]
    )
    return round(cost, 8)


def _check_daily_budget(client_id: Optional[int], model: str, max_tokens: int) -> None:
    """
    Pre-flight check: estimate worst-case cost and compare against the
    rolling 24-hour spend for this client.  Raises CostBudgetExceeded if
    the budget would be exceeded.

    This runs *before* the API call so we never fire a request we can't afford.
    """
    if client_id is None:
        return  # System-level calls are not client-budget-gated

    estimated_cost = _calculate_cost(model, max_tokens, max_tokens)
    if estimated_cost > SINGLE_CALL_BUDGET_USD:
        raise CostBudgetExceeded(
            f"Single call estimated cost ${estimated_cost:.4f} exceeds limit "
            f"${SINGLE_CALL_BUDGET_USD:.2f} for model {model} / max_tokens {max_tokens}"
        )

    # Check rolling 24h spend — requires Flask app context for DB access.
    try:
        from data.db import query_one
        row = query_one(
            """SELECT COALESCE(SUM(cost_usd), 0) AS total
               FROM llm_usage
               WHERE client_id = ?
                 AND recorded_at >= datetime('now', '-1 day')""",
            (client_id,),
        )
        daily_spend = float(row["total"]) if row else 0.0
        if daily_spend + estimated_cost > DAILY_CLIENT_BUDGET_USD:
            raise CostBudgetExceeded(
                f"Client {client_id} rolling 24h spend ${daily_spend:.4f} + "
                f"estimated ${estimated_cost:.4f} would exceed daily limit "
                f"${DAILY_CLIENT_BUDGET_USD:.2f}"
            )
    except CostBudgetExceeded:
        raise
    except Exception as exc:
        # DB not available (e.g. outside Flask context) — log and continue
        logger.warning("Cost pre-flight DB check skipped: %s", exc)


def _record_usage(
    *,
    client_id: Optional[int],
    staff_slug: Optional[str],
    workflow: Optional[str],
    trace_id: Optional[str],
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int,
    cache_write_tokens: int,
    cost_usd: float,
    status: str,
    latency_ms: int,
    error_message: Optional[str] = None,
) -> None:
    """Persist one usage record to llm_usage.  Best-effort — never raises."""
    try:
        from data.db import insert
        insert(
            """INSERT INTO llm_usage
               (client_id, staff_slug, workflow, trace_id, model,
                input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
                cost_usd, status, latency_ms, error_message)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                client_id, staff_slug, workflow, trace_id, model,
                input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
                cost_usd, status, latency_ms, error_message,
            ),
        )
    except Exception as exc:
        logger.error("Failed to record LLM usage: %s", exc)


def tracked_completion(
    client,
    *,
    model: str,
    max_tokens: int,
    messages: list,
    system: str = "",
    # Attribution
    client_id: Optional[int] = None,
    staff_slug: Optional[str] = None,
    workflow: Optional[str] = None,
    trace_id: Optional[str] = None,
    **kwargs,
):
    """
    Drop-in wrapper around `client.messages.create()` that:
      1. Runs a pre-flight budget check.
      2. Times the call.
      3. Records token usage and cost to `llm_usage`.
      4. Returns the original Anthropic Message object unchanged.

    All extra kwargs are forwarded to the underlying API call.
    """
    _check_daily_budget(client_id, model, max_tokens)

    start_ms = time.monotonic()
    status = "success"
    error_message = None
    response = None

    create_kwargs = dict(
        model=model,
        max_tokens=max_tokens,
        messages=messages,
        **kwargs,
    )
    if system:
        create_kwargs["system"] = system

    try:
        response = client.messages.create(**create_kwargs)
    except Exception as exc:
        status = "error"
        error_message = str(exc)
        logger.error(
            "Claude API error [client=%s workflow=%s]: %s",
            client_id, workflow, exc,
        )
        raise
    finally:
        latency_ms = int((time.monotonic() - start_ms) * 1000)

        if response is not None:
            usage = response.usage
            input_tokens       = getattr(usage, "input_tokens", 0)
            output_tokens      = getattr(usage, "output_tokens", 0)
            cache_read_tokens  = getattr(usage, "cache_read_input_tokens", 0)
            cache_write_tokens = getattr(usage, "cache_creation_input_tokens", 0)
        else:
            input_tokens = output_tokens = cache_read_tokens = cache_write_tokens = 0

        cost_usd = _calculate_cost(
            model, input_tokens, output_tokens,
            cache_read_tokens, cache_write_tokens,
        )

        _record_usage(
            client_id=client_id,
            staff_slug=staff_slug,
            workflow=workflow,
            trace_id=trace_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            cost_usd=cost_usd,
            status=status,
            latency_ms=latency_ms,
            error_message=error_message,
        )

        logger.info(
            "LLM call | client=%s staff=%s workflow=%s model=%s "
            "tokens_in=%d tokens_out=%d cost=$%.6f latency=%dms status=%s",
            client_id, staff_slug, workflow, model,
            input_tokens, output_tokens, cost_usd, latency_ms, status,
        )

    return response
