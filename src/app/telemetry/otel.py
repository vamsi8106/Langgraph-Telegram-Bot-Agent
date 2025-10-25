# src/app/telemetry/otel.py
"""
OpenTelemetry tracing setup for the Karan bot.

This module configures the OTLP exporter (if available) and integrates
logging spans. It provides helpers to obtain tracers and current trace IDs
for Prometheus exemplars.
"""

from __future__ import annotations

import logging
import socket
from urllib.parse import urlparse

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor

from ..config.settings import settings

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _reachable(url: str, timeout: float = 0.5) -> bool:
    """
    Check if an OTLP endpoint is reachable via TCP connection.

    Parameters
    ----------
    url : str
        Endpoint URL (e.g., "http://otel-collector:4318").
    timeout : float
        Timeout in seconds for the connection attempt.

    Returns
    -------
    bool
        True if reachable, False otherwise.
    """
    try:
        parsed = urlparse(url)
        host, port = parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Tracing setup
# ---------------------------------------------------------------------------

def init_tracing() -> None:
    """
    Initialize OpenTelemetry tracing if enabled in settings.

    - Sets up the OTLP HTTP exporter if reachable.
    - Registers Batch or Simple span processor.
    - Instruments Python logging for trace correlation.
    """
    if not settings.enable_tracing or not settings.otlp_endpoint:
        _log.info("Tracing disabled.")
        return

    resource = Resource.create({
        "service.name": settings.service_name,
        "service.namespace": "chat-bot",
        "deployment.environment": settings.env,
    })

    provider = TracerProvider(resource=resource)

    # Use OTLP exporter if reachable, else a no-op exporter.
    if _reachable(settings.otlp_endpoint):
        exporter = OTLPSpanExporter(
            endpoint=f"{settings.otlp_endpoint}/v1/traces",
            timeout=2,
        )
        processor = BatchSpanProcessor(
            exporter,
            schedule_delay_millis=3000,
            max_export_batch_size=512,
            exporter_timeout_millis=2000,
        )
        provider.add_span_processor(processor)
        _log.info("Tracing initialized with OTLP endpoint=%s", settings.otlp_endpoint)
    else:
        provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter(endpoint="http://invalid")))
        _log.warning("OTLP %s not reachable; using no-op exporter.", settings.otlp_endpoint)

    trace.set_tracer_provider(provider)

    # Integrate tracing context into logs
    try:
        LoggingInstrumentor().instrument(set_logging_format=False)
    except Exception:  # pragma: no cover
        pass


def get_tracer(name: str = "app"):
    """
    Get a named OpenTelemetry tracer.

    Parameters
    ----------
    name : str
        Logical name for the tracer (default: "app").

    Returns
    -------
    Tracer
        Configured OpenTelemetry tracer instance.
    """
    return trace.get_tracer(name)


def current_trace_id_hex() -> str | None:
    """
    Return the current active span’s trace ID in hex (32 chars), if available.

    Returns
    -------
    Optional[str]
        32-character trace ID string or None if no active span.
    """
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.is_valid:
        return f"{ctx.trace_id:032x}"
    return None
