"""
observability/flask_middleware.py
──────────────────────────────────
Registers OpenTelemetry instrumentation on the Flask app.

Instruments:
  - Every inbound HTTP request (via opentelemetry-instrumentation-flask)
  - Every outbound requests.Session call (via opentelemetry-instrumentation-requests)
  - SQLite queries via a lightweight manual wrapper on data/db.py

Call register_flask_instrumentation(app) once in create_app(), after
blueprints are registered.
"""

import logging
from flask import Flask

logger = logging.getLogger(__name__)


def register_flask_instrumentation(app: Flask) -> None:
    """
    Attach OTel auto-instrumentation to a Flask app instance.
    Safe to call even if the OTel packages are not installed — it degrades
    gracefully so the app continues to run without tracing.
    """
    _instrument_flask(app)
    _instrument_requests()
    logger.info("OpenTelemetry Flask instrumentation registered.")


def _instrument_flask(app: Flask) -> None:
    try:
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        FlaskInstrumentor().instrument_app(
            app,
            excluded_urls="/health,/static/*",
        )
        logger.debug("FlaskInstrumentor active.")
    except ImportError:
        logger.warning(
            "opentelemetry-instrumentation-flask not installed; "
            "HTTP request tracing disabled."
        )
    except Exception as exc:
        logger.error("FlaskInstrumentor failed: %s", exc)


def _instrument_requests() -> None:
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        RequestsInstrumentor().instrument()
        logger.debug("RequestsInstrumentor active.")
    except ImportError:
        logger.warning(
            "opentelemetry-instrumentation-requests not installed; "
            "outbound HTTP tracing disabled."
        )
    except Exception as exc:
        logger.error("RequestsInstrumentor failed: %s", exc)
