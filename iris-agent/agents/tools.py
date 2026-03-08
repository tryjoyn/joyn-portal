"""
iris-agent/agents/tools.py
──────────────────────────
Tool registry for the Iris SupervisorAgent.

Each tool is:
  1. Defined as a JSON schema (for the Anthropic tool-calling API).
  2. Implemented as a Python function that the supervisor dispatches to.

All tools are instrumented with OpenTelemetry step spans from the
Phase 1 observability layer.

Tools
-----
  fetch_client_profile      — Pull client settings + jurisdiction list from portal DB
  assess_regulatory_impact  — Score a bulletin's impact for a specific client
  route_action              — Decide and execute the correct output action (IMMEDIATE/DIGEST/MONITOR)
  log_activity              — Write a structured activity record back to the portal
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

# ── Portal connectivity ────────────────────────────────────────────────────────

PORTAL_URL    = os.environ.get("JOYN_PORTAL_URL", "").rstrip("/")
PORTAL_SECRET = os.environ.get("JOYN_PORTAL_SECRET", "")

def _portal_headers() -> dict:
    """Return auth headers for portal API calls, with OTel trace propagation."""
    headers = {
        "Content-Type": "application/json",
        "X-Joyn-Secret": PORTAL_SECRET,
    }
    # Inject W3C traceparent/tracestate so portal spans link to this trace
    try:
        from observability.tracing import inject_trace_context
        headers = inject_trace_context(headers)
    except ImportError:
        pass
    return headers


# ── JSON schemas (sent to Claude) ─────────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "name": "fetch_client_profile",
        "description": (
            "Retrieve a client's profile from the Joyn portal, including their "
            "company name, subscribed jurisdictions (states), alert preferences, "
            "and Iris configuration settings. Call this first before any analysis."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "The Joyn portal client ID."
                }
            },
            "required": ["client_id"]
        }
    },
    {
        "name": "assess_regulatory_impact",
        "description": (
            "Analyse a regulatory bulletin and determine its impact on a specific "
            "client. Returns a priority level (IMMEDIATE / DIGEST / MONITOR), "
            "a plain-English impact summary, recommended actions, and affected "
            "lines of business. Use the client profile to filter by jurisdiction "
            "and line of business relevance."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "The Joyn portal client ID."
                },
                "bulletin": {
                    "type": "object",
                    "description": "The raw regulatory bulletin object.",
                    "properties": {
                        "id":           {"type": "string"},
                        "title":        {"type": "string"},
                        "state":        {"type": "string"},
                        "source":       {"type": "string"},
                        "published_at": {"type": "string"},
                        "content":      {"type": "string"},
                        "url":          {"type": "string"}
                    },
                    "required": ["title", "state", "content"]
                },
                "client_jurisdictions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of state codes the client is licensed in."
                },
                "client_lines_of_business": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lines of business the client operates (e.g. ['P&C', 'Life'])."
                }
            },
            "required": ["client_id", "bulletin", "client_jurisdictions"]
        }
    },
    {
        "name": "route_action",
        "description": (
            "Execute the appropriate output action based on the assessed priority. "
            "IMMEDIATE → post a high-priority alert to the portal activity log and "
            "trigger an email notification. "
            "DIGEST → queue the item for the next weekly digest. "
            "MONITOR → record for trend tracking only, no client notification."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "The Joyn portal client ID."
                },
                "priority": {
                    "type": "string",
                    "enum": ["IMMEDIATE", "DIGEST", "MONITOR"],
                    "description": "Priority level from assess_regulatory_impact."
                },
                "bulletin_title": {
                    "type": "string",
                    "description": "Short title of the bulletin."
                },
                "impact_summary": {
                    "type": "string",
                    "description": "Plain-English summary of the regulatory impact."
                },
                "recommended_actions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of concrete steps the client should take."
                },
                "bulletin_url": {
                    "type": "string",
                    "description": "Source URL of the bulletin."
                }
            },
            "required": ["client_id", "priority", "bulletin_title", "impact_summary"]
        }
    },
    {
        "name": "log_activity",
        "description": (
            "Write a structured activity record to the Joyn portal for the client "
            "dashboard. Use this to record any significant action Iris has taken, "
            "including analysis completions, skipped bulletins, and errors."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "integer",
                    "description": "The Joyn portal client ID."
                },
                "action_type": {
                    "type": "string",
                    "enum": ["analysis", "alert", "digest", "monitor", "error", "info"],
                    "description": "Category of the activity."
                },
                "action_description": {
                    "type": "string",
                    "description": "Human-readable description of what Iris did."
                },
                "status": {
                    "type": "string",
                    "enum": ["complete", "pending", "failed"],
                    "description": "Outcome status."
                }
            },
            "required": ["client_id", "action_type", "action_description"]
        }
    }
]


# ── Tool implementations ───────────────────────────────────────────────────────

def fetch_client_profile(client_id: int, tracer=None) -> dict:
    """
    Fetch client profile from the portal API.
    Falls back to a structured mock when JOYN_PORTAL_URL is not set (dev/test).
    """
    _span = _get_step_span(tracer, "fetch_client_profile", client_id=client_id)

    if not PORTAL_URL:
        logger.warning("JOYN_PORTAL_URL not set — returning mock client profile")
        mock = {
            "client_id": client_id,
            "company_name": f"Mock Insurance Co. (client {client_id})",
            "primary_contact_name": "Test User",
            "jurisdictions": ["FL", "TX", "CA"],
            "lines_of_business": ["P&C", "Life"],
            "alert_frequency": "immediate",
            "iris_settings": {
                "alert_email": "test@example.com",
                "alert_frequency": "immediate",
                "status": "active"
            },
            "_mock": True
        }
        _close_span(_span, mock)
        return mock

    try:
        resp = requests.get(
            f"{PORTAL_URL}/api/iris/client/{client_id}/profile",
            headers=_portal_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        _close_span(_span, data)
        return data
    except Exception as exc:
        logger.error("fetch_client_profile failed for client %s: %s", client_id, exc)
        _close_span(_span, {"error": str(exc)}, error=True)
        return {"error": str(exc), "client_id": client_id}


def assess_regulatory_impact(
    client_id: int,
    bulletin: dict,
    client_jurisdictions: list,
    client_lines_of_business: Optional[list] = None,
    tracer=None,
    anthropic_client=None,
    model: str = "claude-sonnet-4-5",
    workflow: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> dict:
    """
    Use Claude to assess the regulatory impact of a bulletin for a specific client.
    Uses tracked_completion() from Phase 1 for cost tracking.
    """
    _span = _get_step_span(
        tracer, "assess_regulatory_impact",
        client_id=client_id,
        bulletin_state=bulletin.get("state", ""),
        bulletin_title=bulletin.get("title", "")[:80],
    )

    # Fast-path: skip if bulletin state not in client jurisdictions
    bulletin_state = bulletin.get("state", "").upper()
    if bulletin_state and client_jurisdictions:
        if bulletin_state not in [j.upper() for j in client_jurisdictions]:
            result = {
                "priority": "MONITOR",
                "impact_summary": (
                    f"Bulletin is for {bulletin_state}, which is outside the client's "
                    f"licensed jurisdictions ({', '.join(client_jurisdictions)}). "
                    "No action required."
                ),
                "recommended_actions": [],
                "affected_lines_of_business": [],
                "jurisdiction_filtered": True,
            }
            _close_span(_span, result)
            return result

    if anthropic_client is None:
        import anthropic
        anthropic_client = anthropic.Anthropic()

    lob_str = ", ".join(client_lines_of_business or ["not specified"])
    jurisdictions_str = ", ".join(client_jurisdictions)

    system_prompt = (
        "You are Iris, an expert insurance regulatory analyst. "
        "Analyse regulatory bulletins and assess their impact on insurance companies. "
        "Be precise, actionable, and concise. Always respond with valid JSON only."
    )

    user_prompt = f"""Analyse this regulatory bulletin for an insurance company.

CLIENT CONTEXT:
- Licensed jurisdictions: {jurisdictions_str}
- Lines of business: {lob_str}

BULLETIN:
Title: {bulletin.get('title', 'N/A')}
State: {bulletin.get('state', 'N/A')}
Source: {bulletin.get('source', 'N/A')}
Published: {bulletin.get('published_at', 'N/A')}
URL: {bulletin.get('url', 'N/A')}

Content:
{bulletin.get('content', 'No content provided')}

Respond with JSON only (no markdown):
{{
  "priority": "IMMEDIATE" | "DIGEST" | "MONITOR",
  "impact_summary": "2-3 sentence plain-English summary",
  "recommended_actions": ["action 1", "action 2"],
  "affected_lines_of_business": ["P&C", "Life"],
  "compliance_deadline": "YYYY-MM-DD or null",
  "confidence": 0.0-1.0
}}

Priority guide:
- IMMEDIATE: Compliance deadline within 30 days, significant financial/operational impact
- DIGEST: Important but not urgent, include in weekly summary
- MONITOR: Low impact or informational only"""

    try:
        from observability.cost_tracker import tracked_completion
        response = tracked_completion(
            anthropic_client,
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            client_id=client_id,
            staff_slug="iris",
            workflow=workflow or "bulletin_analysis",
            trace_id=trace_id,
        )
    except ImportError:
        # Outside portal context — use raw client
        response = anthropic_client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("assess_regulatory_impact: non-JSON response, defaulting to MONITOR")
        result = {
            "priority": "MONITOR",
            "impact_summary": raw[:500],
            "recommended_actions": [],
            "affected_lines_of_business": [],
            "parse_error": True,
        }

    _close_span(_span, result)
    return result


def route_action(
    client_id: int,
    priority: str,
    bulletin_title: str,
    impact_summary: str,
    recommended_actions: Optional[list] = None,
    bulletin_url: Optional[str] = None,
    tracer=None,
) -> dict:
    """
    Execute the correct output action based on priority level.
    Calls the portal's /api/log/output and /api/log/activity endpoints.
    """
    _span = _get_step_span(
        tracer, "route_action",
        client_id=client_id,
        priority=priority,
    )

    actions_text = ""
    if recommended_actions:
        actions_text = "\n\nRecommended actions:\n" + "\n".join(
            f"• {a}" for a in recommended_actions
        )

    result = {"client_id": client_id, "priority": priority, "portal_logged": False}

    if priority == "IMMEDIATE":
        # Post a high-priority output to the portal
        if PORTAL_URL:
            try:
                payload = {
                    "client_id": client_id,
                    "staff_name": "Iris",
                    "staff_slug": "iris",
                    "output_type": "alert",
                    "title": f"[IMMEDIATE] {bulletin_title}",
                    "summary": impact_summary,
                    "severity": "high",
                    "full_content": (
                        f"{impact_summary}{actions_text}"
                        + (f"\n\nSource: {bulletin_url}" if bulletin_url else "")
                    ),
                }
                resp = requests.post(
                    f"{PORTAL_URL}/api/log/output",
                    json=payload,
                    headers=_portal_headers(),
                    timeout=10,
                )
                resp.raise_for_status()
                result["portal_logged"] = True
                result["output_id"] = resp.json().get("id")
            except Exception as exc:
                logger.error("route_action IMMEDIATE portal call failed: %s", exc)
                result["portal_error"] = str(exc)
        else:
            logger.info(
                "[IMMEDIATE] client=%s | %s | %s",
                client_id, bulletin_title, impact_summary
            )
            result["portal_logged"] = False
            result["note"] = "JOYN_PORTAL_URL not set — logged locally only"

    elif priority == "DIGEST":
        # Log to activity as a pending digest item
        if PORTAL_URL:
            try:
                payload = {
                    "client_id": client_id,
                    "staff_name": "Iris",
                    "staff_slug": "iris",
                    "action_type": "digest",
                    "action_description": f"Queued for digest: {bulletin_title}",
                    "status": "pending",
                }
                resp = requests.post(
                    f"{PORTAL_URL}/api/log/activity",
                    json=payload,
                    headers=_portal_headers(),
                    timeout=10,
                )
                resp.raise_for_status()
                result["portal_logged"] = True
                result["activity_id"] = resp.json().get("id")
            except Exception as exc:
                logger.error("route_action DIGEST portal call failed: %s", exc)
                result["portal_error"] = str(exc)
        else:
            logger.info("[DIGEST] client=%s | %s", client_id, bulletin_title)
            result["note"] = "JOYN_PORTAL_URL not set — logged locally only"

    else:  # MONITOR
        logger.info("[MONITOR] client=%s | %s", client_id, bulletin_title)
        result["note"] = "Recorded for trend tracking — no client notification"

    _close_span(_span, result)
    return result


def log_activity(
    client_id: int,
    action_type: str,
    action_description: str,
    status: str = "complete",
    tracer=None,
) -> dict:
    """Write a structured activity record to the portal."""
    _span = _get_step_span(
        tracer, "log_activity",
        client_id=client_id,
        action_type=action_type,
    )

    result = {"client_id": client_id, "logged": False}

    if PORTAL_URL:
        try:
            payload = {
                "client_id": client_id,
                "staff_name": "Iris",
                "staff_slug": "iris",
                "action_type": action_type,
                "action_description": action_description,
                "status": status,
            }
            resp = requests.post(
                f"{PORTAL_URL}/api/log/activity",
                json=payload,
                headers=_portal_headers(),
                timeout=10,
            )
            resp.raise_for_status()
            result["logged"] = True
            result["activity_id"] = resp.json().get("id")
        except Exception as exc:
            logger.error("log_activity portal call failed: %s", exc)
            result["error"] = str(exc)
    else:
        logger.info(
            "log_activity [%s] client=%s: %s (%s)",
            action_type, client_id, action_description, status
        )
        result["note"] = "JOYN_PORTAL_URL not set — logged locally only"

    _close_span(_span, result)
    return result


# ── Tool dispatcher ────────────────────────────────────────────────────────────

TOOL_FUNCTIONS = {
    "fetch_client_profile":    fetch_client_profile,
    "assess_regulatory_impact": assess_regulatory_impact,
    "route_action":            route_action,
    "log_activity":            log_activity,
}


def dispatch_tool(
    tool_name: str,
    tool_input: dict,
    *,
    tracer=None,
    anthropic_client=None,
    model: str = "claude-sonnet-4-5",
    workflow: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> Any:
    """
    Dispatch a tool call from the supervisor loop.
    Injects tracer and anthropic_client into tools that need them.
    """
    fn = TOOL_FUNCTIONS.get(tool_name)
    if fn is None:
        raise ValueError(f"Unknown tool: {tool_name!r}")

    # Inject shared context into tools that accept it
    kwargs = dict(tool_input)
    kwargs["tracer"] = tracer

    if tool_name == "assess_regulatory_impact":
        kwargs["anthropic_client"] = anthropic_client
        kwargs["model"] = model
        kwargs["workflow"] = workflow
        kwargs["trace_id"] = trace_id

    return fn(**kwargs)


# ── OTel helpers (graceful no-op if tracing not available) ────────────────────

def _get_step_span(tracer, step_name: str, **attrs):
    """Start a step span if a tracer is provided, else return None."""
    if tracer is None:
        return None
    try:
        from observability.tracing import step_span as _step_span
        ctx = _step_span(tracer, step_name, **{str(k): str(v) for k, v in attrs.items()})
        return ctx.__enter__()
    except Exception:
        return None


def _close_span(span_ctx, result: Any, error: bool = False):
    """Close a step span context if one was opened."""
    if span_ctx is None:
        return
    try:
        from opentelemetry.trace import StatusCode
        if error:
            span_ctx.set_status(StatusCode.ERROR)
        else:
            span_ctx.set_status(StatusCode.OK)
        # Attach priority to span for easy filtering in trace UIs
        if isinstance(result, dict) and "priority" in result:
            span_ctx.set_attribute("iris.priority", result["priority"])
    except Exception:
        pass
