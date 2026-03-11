"""
observability/tracing.py
────────────────────────
OpenTelemetry-based distributed tracing for the Joyn/Iris platform.

Architecture
────────────
Every Iris workflow run is wrapped in a root span.  Each discrete step
(fetch_bulletins, analyse_bulletin, assess_impact, deliver_briefing) is
a child span.  All spans carry standard attributes for client_id,
staff_slug, and workflow name so traces can be filtered by client in
any OTLP-compatible backend (Jaeger, Grafana Tempo, Datadog, etc.).

When no OTLP exporter is configured (local dev), spans are emitted to
stdout via ConsoleSpanExporter so developers can see trace data without
any external service.

Usage
─────
    from observability.tracing import get_tracer, workflow_span, step_span

    tracer = get_tracer()

    with workflow_span(tracer, "bulletin_analysis", client_id=42, staff_slug="iris") as span:
        span.set_attribute("bulletin.count", 5)

        with step_span(tracer, "fetch_bulletins") as step:
            step.set_attribute("source", "NAIC")
            bulletins = fetch_bulletins(...)

        with step_span(tracer, "analyse_bulletin") as step:
            step.set_attribute("bulletin.id", bulletin_id)
            result = analyse(...)

Environment variables
─────────────────────
OTLP_ENDPOINT       OTLP/gRPC endpoint, e.g. http://localhost:4317
                    If unset, falls back to ConsoleSpanExporter.
OTLP_HEADERS        Optional comma-separated key=value pairs for auth,
                    e.g. "x-honeycomb-team=abc123"
OTEL_SERVICE_NAME   Defaults to "joyn-iris"
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)

# ── Lazy initialisation ────────────────────────────────────────────────────────
_tracer_provider = None


def _build_provider():
    """Initialise the TracerProvider once.  Called on first get_tracer()."""
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME

    service_name = os.environ.get("OTEL_SERVICE_NAME", "joyn-iris")
    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)

    otlp_endpoint = os.environ.get("OTLP_ENDPOINT", "")
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            headers_raw = os.environ.get("OTLP_HEADERS", "")
            headers = {}
            if headers_raw:
                for pair in headers_raw.split(","):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        headers[k.strip()] = v.strip()

            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, headers=headers)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OpenTelemetry: OTLP exporter configured → %s", otlp_endpoint)
        except ImportError:
            logger.warning(
                "opentelemetry-exporter-otlp-proto-grpc not installed; "
                "falling back to ConsoleSpanExporter"
            )
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        # Development fallback — print spans to stdout
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("OpenTelemetry: ConsoleSpanExporter active (set OTLP_ENDPOINT to ship traces)")

    trace.set_tracer_provider(provider)
    return provider


def get_tracer(name: str = "joyn.iris"):
    """Return a tracer, initialising the provider on first call."""
    global _tracer_provider
    if _tracer_provider is None:
        try:
            _tracer_provider = _build_provider()
        except Exception as exc:
            logger.error("Failed to initialise OpenTelemetry provider: %s", exc)
            # Return a no-op tracer so the app still runs
            from opentelemetry import trace
            return trace.get_tracer(name)

    from opentelemetry import trace
    return trace.get_tracer(name)


# ── Span helpers ───────────────────────────────────────────────────────────────

@contextmanager
def workflow_span(
    tracer,
    workflow_name: str,
    *,
    client_id: Optional[int] = None,
    staff_slug: Optional[str] = None,
    trace_id_out: Optional[list] = None,
):
    """
    Context manager for a top-level workflow span.

    Parameters
    ----------
    tracer          : OpenTelemetry Tracer
    workflow_name   : Human-readable name, e.g. "bulletin_analysis"
    client_id       : Joyn client ID for attribution
    staff_slug      : e.g. "iris"
    trace_id_out    : Optional single-element list; populated with the
                      hex trace_id so callers can store it for correlation.

    Example
    -------
        with workflow_span(tracer, "bulletin_analysis", client_id=42) as span:
            span.set_attribute("bulletin.count", 3)
    """
    from opentelemetry import trace
    from opentelemetry.trace import StatusCode

    with tracer.start_as_current_span(f"iris.workflow.{workflow_name}") as span:
        if client_id is not None:
            span.set_attribute("joyn.client_id", client_id)
        if staff_slug:
            span.set_attribute("joyn.staff_slug", staff_slug)
        span.set_attribute("joyn.workflow", workflow_name)

        # Expose trace_id to caller for storage in llm_usage / activity_log
        ctx = span.get_span_context()
        hex_trace_id = format(ctx.trace_id, "032x") if ctx.is_valid else None
        if trace_id_out is not None and hex_trace_id:
            trace_id_out.append(hex_trace_id)

        try:
            yield span
        except Exception as exc:
            span.set_status(StatusCode.ERROR, str(exc))
            span.record_exception(exc)
            raise


@contextmanager
def step_span(tracer, step_name: str, **attributes):
    """
    Context manager for a child step span within a workflow.

    Example
    -------
        with step_span(tracer, "fetch_bulletins", source="NAIC", state="CA") as span:
            bulletins = fetch(...)
    """
    from opentelemetry.trace import StatusCode

    with tracer.start_as_current_span(f"iris.step.{step_name}") as span:
        for key, value in attributes.items():
            span.set_attribute(key, str(value))
        try:
            yield span
        except Exception as exc:
            span.set_status(StatusCode.ERROR, str(exc))
            span.record_exception(exc)
            raise


def inject_trace_context(headers: dict) -> dict:
    """
    Inject W3C TraceContext headers into an outgoing HTTP request dict.
    Use this when calling external services (e.g. the Iris Railway backend)
    so traces propagate across service boundaries.

    Example
    -------
        headers = inject_trace_context({"X-Joyn-Secret": secret})
        requests.post(url, json=payload, headers=headers)
    """
    try:
        from opentelemetry.propagate import inject
        inject(headers)
    except Exception as exc:
        logger.warning("Failed to inject trace context: %s", exc)
    return headers


def extract_trace_id() -> Optional[str]:
    """
    Return the current active trace ID as a hex string, or None if no
    active span exists.  Useful for correlating log lines with traces.
    """
    try:
        from opentelemetry import trace
        ctx = trace.get_current_span().get_span_context()
        if ctx.is_valid:
            return format(ctx.trace_id, "032x")
    except Exception:
        pass
    return None
