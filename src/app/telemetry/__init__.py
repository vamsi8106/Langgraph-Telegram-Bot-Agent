# # src/app/telemetry/__init__.py
# from .otel import init_tracing as _init_tracing, get_tracer, current_trace_id_hex
# from ..metrics import start_metrics_server

# def init_telemetry():
#     _init_tracing()
#     start_metrics_server()

# __all__ = ["init_telemetry", "get_tracer", "current_trace_id_hex"]


# src/app/telemetry/__init__.py
"""
Telemetry initialization module.

Combines tracing (OpenTelemetry) and Prometheus metrics setup into a single
entrypoint via `init_telemetry()`, used at app startup.

Exports
-------
- init_telemetry : initialize tracing and metrics.
- get_tracer : obtain an OpenTelemetry tracer.
- current_trace_id_hex : retrieve the current trace ID for exemplars.
"""

from .otel import init_tracing as _init_tracing, get_tracer, current_trace_id_hex
from ..metrics import start_metrics_server


def init_telemetry() -> None:
    """
    Initialize unified telemetry:
      • Starts OpenTelemetry tracing (if enabled).
      • Starts the Prometheus metrics server (if enabled).
    """
    _init_tracing()
    start_metrics_server()


__all__ = ["init_telemetry", "get_tracer", "current_trace_id_hex"]
