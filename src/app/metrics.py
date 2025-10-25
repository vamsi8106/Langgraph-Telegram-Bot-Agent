# # src/app/metrics.py
# import threading
# from prometheus_client import Counter, Histogram, Gauge, start_http_server
# from .config.settings import settings

# # Read trace id directly from OpenTelemetry to avoid circular import
# try:
#     from opentelemetry import trace  # optional dependency
# except Exception:  # pragma: no cover
#     trace = None

# NS = settings.metrics_namespace

# # Core app metrics
# TG_UPDATES   = Counter(f"{NS}_tg_updates_total", "Total Telegram updates", ["type"])
# LLM_CALLS    = Counter(f"{NS}_llm_calls_total", "Total LLM calls", ["model", "status"])
# LLM_LAT      = Histogram(f"{NS}_llm_latency_seconds", "LLM latency seconds", ["model"])
# GRAPH_LAT    = Histogram(f"{NS}_graph_latency_seconds", "Graph invoke latency")
# HANDLER_LAT  = Histogram(f"{NS}_handler_latency_seconds", "Handler latency seconds", ["handler"])

# # Static service info (useful in Grafana filters)
# SERVICE_INFO = Gauge(
#     f"{NS}_service_info",
#     "Service metadata",
#     ["service_name", "env", "version"]
# )

# def _exemplar_kv():
#     """Return exemplar dict with trace_id when there is an active OTel trace; else None."""
#     if trace is None:
#         return None
#     try:
#         span = trace.get_current_span()
#         ctx = span.get_span_context()
#         # In OTel, 'is_valid' is a property; guard defensively
#         if ctx and getattr(ctx, "is_valid", False):
#             return {"trace_id": f"{ctx.trace_id:032x}"}
#     except Exception:
#         pass
#     return None

# def observe(hist: Histogram, value: float, **labels):
#     """Observe with exemplar if available (prometheus_client >= 0.20 supports exemplars)."""
#     h = hist.labels(**labels) if labels else hist
#     exemplar = _exemplar_kv()
#     try:
#         if exemplar:
#             h.observe(value, exemplar=exemplar)
#         else:
#             h.observe(value)
#     except TypeError:
#         # Older prometheus_client without exemplar support
#         h.observe(value)

# def inc(counter: Counter, **labels):
#     """Increment counter (no exemplar support in python client)."""
#     (counter.labels(**labels) if labels else counter).inc()

# def start_metrics_server():
#     """Start Prometheus /metrics HTTP server if enabled (idempotent)."""
#     if not settings.enable_prometheus:
#         return
#     if getattr(start_metrics_server, "_started", False):
#         return
#     start_metrics_server._started = True
#     t = threading.Thread(target=start_http_server, args=(settings.prometheus_port,), daemon=True)
#     t.start()

# src/app/metrics.py
"""
Prometheus metrics for the Karan bot.

Includes counters, histograms, and a small helper API:
- observe(hist, value, **labels): record a value (with OTel trace exemplar if available)
- inc(counter, **labels): increment a labeled counter
- start_metrics_server(): start the /metrics HTTP server (idempotent)
"""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional

from prometheus_client import Counter, Gauge, Histogram, start_http_server

from .config.settings import settings

# Read trace id directly from OpenTelemetry to avoid circular import
try:
    from opentelemetry import trace  # optional dependency
except Exception:  # pragma: no cover
    trace = None

NS = settings.metrics_namespace

# ---------------- Core app metrics ----------------

TG_UPDATES = Counter(f"{NS}_tg_updates_total", "Total Telegram updates", ["type"])
LLM_CALLS = Counter(f"{NS}_llm_calls_total", "Total LLM calls", ["model", "status"])
LLM_LAT = Histogram(f"{NS}_llm_latency_seconds", "LLM latency seconds", ["model"])
GRAPH_LAT = Histogram(f"{NS}_graph_latency_seconds", "Graph invoke latency")
HANDLER_LAT = Histogram(
    f"{NS}_handler_latency_seconds", "Handler latency seconds", ["handler"]
)

# Static service info (useful in Grafana filters)
SERVICE_INFO = Gauge(
    f"{NS}_service_info",
    "Service metadata",
    ["service_name", "env", "version"],
)

# Optionally set fixed labels once (safe to call multiple times)
try:
    SERVICE_INFO.labels(
        service_name=settings.service_name, env=settings.env, version="unknown"
    ).set(1)
except Exception:  # pragma: no cover
    pass


# ---------------- Helper functions ----------------

def _exemplar_kv() -> Optional[Dict[str, str]]:
    """
    Return an exemplar dict with trace_id when an active OTel span exists; else None.
    """
    if trace is None:
        return None
    try:
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and getattr(ctx, "is_valid", False):
            return {"trace_id": f"{ctx.trace_id:032x}"}
    except Exception:  # pragma: no cover
        pass
    return None


def observe(hist: Histogram, value: float, **labels: Any) -> None:
    """
    Observe a histogram value with an optional OpenTelemetry trace exemplar.

    Parameters
    ----------
    hist : Histogram
        Target Prometheus histogram metric.
    value : float
        Value to observe.
    **labels : Any
        Optional labels to apply before observation.
    """
    h = hist.labels(**labels) if labels else hist
    exemplar = _exemplar_kv()
    try:
        if exemplar:
            h.observe(value, exemplar=exemplar)  # requires prometheus_client >= 0.20
        else:
            h.observe(value)
    except TypeError:
        # Older prometheus_client without exemplar support
        h.observe(value)


def inc(counter: Counter, **labels: Any) -> None:
    """
    Increment a counter with optional labels.

    Parameters
    ----------
    counter : Counter
        Target Prometheus counter.
    **labels : Any
        Optional labels to apply before increment.
    """
    (counter.labels(**labels) if labels else counter).inc()


def start_metrics_server() -> None:
    """
    Start the Prometheus /metrics HTTP server if enabled (idempotent).
    """
    if not settings.enable_prometheus:
        return
    if getattr(start_metrics_server, "_started", False):
        return
    start_metrics_server._started = True
    thread = threading.Thread(
        target=start_http_server, args=(settings.prometheus_port,), daemon=True
    )
    thread.start()
