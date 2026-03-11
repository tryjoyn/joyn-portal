"""
iris-agent/agents/supervisor.py
────────────────────────────────
SupervisorAgent — the Coordinator-pattern core loop for Iris.

Architecture (per benchmark Phase 2 target):
  1. Receive a job: { client_id, bulletins: [...] }
  2. Open a top-level OTel workflow span for full traceability.
  3. Enter the Anthropic tool-calling loop:
       a. Send system prompt + bulletin context to Claude.
       b. Claude responds with tool_use blocks.
       c. Dispatch each tool via the tool registry.
       d. Feed tool results back to Claude.
       e. Repeat until Claude returns a text stop_reason (done).
  4. Record cost via Phase 1 tracked_completion().
  5. Return a structured result dict.

Key design decisions:
  - Raw Anthropic SDK only (no LangChain / LiteLLM).
  - All Claude calls go through tracked_completion() for cost tracking.
  - OTel workflow_span wraps the entire job for end-to-end tracing.
  - Max tool iterations capped at 20 to prevent runaway loops.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

import anthropic

logger = logging.getLogger(__name__)

DEFAULT_MODEL    = os.environ.get("IRIS_MODEL", "claude-haiku-3-5")
MAX_ITERATIONS   = int(os.environ.get("IRIS_MAX_ITERATIONS", "20"))
MAX_TOKENS       = int(os.environ.get("IRIS_MAX_TOKENS", "4096"))


class SupervisorAgent:
    """
    Coordinator-pattern supervisor for Iris regulatory analysis.

    Parameters
    ----------
    model : str
        Anthropic model identifier. Defaults to IRIS_MODEL env var or claude-sonnet-4-5.
    max_iterations : int
        Maximum tool-calling iterations before forcing a stop.
    """

    SYSTEM_PROMPT = """You are Iris, an expert AI insurance regulatory analyst built by Joyn.

Your job is to analyse regulatory bulletins and take the correct action for each client.

For each bulletin you receive, you MUST:
1. Call fetch_client_profile to get the client's jurisdictions and settings.
2. Call assess_regulatory_impact to determine priority (IMMEDIATE/DIGEST/MONITOR).
3. Call route_action to execute the correct output action.
4. Call log_activity to record what you did.

Rules:
- Only analyse bulletins relevant to the client's licensed jurisdictions.
- Be precise and actionable — insurance professionals rely on your analysis.
- Never fabricate regulatory requirements. If uncertain, set priority to MONITOR.
- Process all bulletins before concluding.

When you have finished processing all bulletins, respond with a brief plain-text
summary of what you did (e.g. "Processed 3 bulletins: 1 IMMEDIATE, 1 DIGEST, 1 MONITOR.")"""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        max_iterations: int = MAX_ITERATIONS,
    ):
        self.model = model
        self.max_iterations = max_iterations
        self._client = anthropic.Anthropic()

        # Import observability tools — graceful degradation if outside portal context
        try:
            from observability.tracing import get_tracer, workflow_span
            self._tracer = get_tracer("joyn.iris.supervisor")
            self._workflow_span = workflow_span
        except ImportError:
            self._tracer = None
            self._workflow_span = None
            logger.warning(
                "observability.tracing not available — running without OTel tracing"
            )

        try:
            from observability.cost_tracker import tracked_completion
            self._tracked_completion = tracked_completion
        except ImportError:
            self._tracked_completion = None
            logger.warning(
                "observability.cost_tracker not available — running without cost tracking"
            )

    # ── Public API ─────────────────────────────────────────────────────────────

    def run(self, job: dict) -> dict:
        """
        Process a job.

        Parameters
        ----------
        job : dict
            {
              "client_id": int,
              "bulletins": [
                {
                  "id": str,
                  "title": str,
                  "state": str,
                  "source": str,
                  "published_at": str,
                  "content": str,
                  "url": str
                },
                ...
              ]
            }

        Returns
        -------
        dict
            {
              "client_id": int,
              "bulletins_processed": int,
              "summary": str,
              "tool_calls": int,
              "trace_id": str | None,
              "status": "success" | "error",
              "error": str | None
            }
        """
        client_id = job.get("client_id")
        bulletins  = job.get("bulletins", [])

        if not client_id:
            return {"status": "error", "error": "job missing client_id"}

        logger.info(
            "SupervisorAgent.run | client=%s bulletins=%d model=%s",
            client_id, len(bulletins), self.model
        )

        # ── Run inside an OTel workflow span ───────────────────────────────────
        if self._tracer and self._workflow_span:
            trace_id_out: list = []
            with self._workflow_span(
                self._tracer,
                "bulletin_analysis",
                client_id=client_id,
                staff_slug="iris",
                trace_id_out=trace_id_out,
            ) as span:
                span.set_attribute("iris.bulletin_count", len(bulletins))
                span.set_attribute("iris.model", self.model)
                result = self._run_loop(client_id, bulletins, trace_id_out)
        else:
            result = self._run_loop(client_id, bulletins, [])

        return result

    # ── Core tool-calling loop ─────────────────────────────────────────────────

    def _run_loop(
        self,
        client_id: int,
        bulletins: list,
        trace_id_out: list,
    ) -> dict:
        from agents.tools import TOOL_SCHEMAS, dispatch_tool

        trace_id = trace_id_out[0] if trace_id_out else None

        # Build the initial user message
        bulletin_json = json.dumps(bulletins, indent=2, default=str)
        messages = [
            {
                "role": "user",
                "content": (
                    f"Process the following {len(bulletins)} regulatory bulletin(s) "
                    f"for client ID {client_id}.\n\n"
                    f"Bulletins:\n{bulletin_json}"
                )
            }
        ]

        tool_call_count = 0
        final_summary   = ""
        status          = "success"
        error_msg       = None

        try:
            for iteration in range(self.max_iterations):
                response = self._call_claude(
                    messages=messages,
                    client_id=client_id,
                    trace_id=trace_id,
                )

                # Append assistant response to conversation
                messages.append({"role": "assistant", "content": response.content})

                if response.stop_reason == "end_turn":
                    # Claude is done — extract the final text summary
                    for block in response.content:
                        if hasattr(block, "text"):
                            final_summary = block.text
                    logger.info(
                        "SupervisorAgent done | client=%s iterations=%d tools=%d",
                        client_id, iteration + 1, tool_call_count
                    )
                    break

                if response.stop_reason == "tool_use":
                    tool_results = []
                    for block in response.content:
                        if block.type != "tool_use":
                            continue

                        tool_call_count += 1
                        tool_name  = block.name
                        tool_input = block.input

                        logger.info(
                            "Tool call #%d | client=%s tool=%s",
                            tool_call_count, client_id, tool_name
                        )

                        try:
                            result = dispatch_tool(
                                tool_name,
                                tool_input,
                                tracer=self._tracer,
                                anthropic_client=self._client,
                                model=self.model,
                                workflow="bulletin_analysis",
                                trace_id=trace_id,
                            )
                            tool_results.append({
                                "type":        "tool_result",
                                "tool_use_id": block.id,
                                "content":     json.dumps(result, default=str),
                            })
                        except Exception as exc:
                            logger.error(
                                "Tool %s failed for client %s: %s",
                                tool_name, client_id, exc
                            )
                            tool_results.append({
                                "type":        "tool_result",
                                "tool_use_id": block.id,
                                "content":     json.dumps({"error": str(exc)}),
                                "is_error":    True,
                            })

                    messages.append({"role": "user", "content": tool_results})

                else:
                    # Unexpected stop reason
                    logger.warning(
                        "Unexpected stop_reason=%s for client=%s",
                        response.stop_reason, client_id
                    )
                    break

            else:
                logger.warning(
                    "SupervisorAgent hit max_iterations=%d for client=%s",
                    self.max_iterations, client_id
                )
                final_summary = (
                    f"Reached maximum iteration limit ({self.max_iterations}). "
                    "Some bulletins may not have been fully processed."
                )

        except Exception as exc:
            logger.error(
                "SupervisorAgent.run failed for client=%s: %s",
                client_id, exc, exc_info=True
            )
            status    = "error"
            error_msg = str(exc)

        return {
            "client_id":           client_id,
            "bulletins_processed": len(bulletins),
            "summary":             final_summary,
            "tool_calls":          tool_call_count,
            "trace_id":            trace_id,
            "status":              status,
            "error":               error_msg,
        }

    # ── Claude API call ────────────────────────────────────────────────────────

    def _call_claude(
        self,
        messages: list,
        client_id: Optional[int] = None,
        trace_id: Optional[str] = None,
    ):
        """
        Call Claude with tool schemas.
        Uses tracked_completion() when available for cost tracking.
        Falls back to raw client.messages.create() outside portal context.
        """
        from agents.tools import TOOL_SCHEMAS

        kwargs = dict(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=self.SYSTEM_PROMPT,
            messages=messages,
            tools=TOOL_SCHEMAS,
        )

        if self._tracked_completion:
            return self._tracked_completion(
                self._client,
                client_id=client_id,
                staff_slug="iris",
                workflow="bulletin_analysis",
                trace_id=trace_id,
                **kwargs,
            )
        else:
            return self._client.messages.create(**kwargs)
