# src/app/adapters/llm_openai.py
import time
from typing import Any, Sequence

from langchain_openai import ChatOpenAI

from ..config.settings import settings
from ..metrics import LLM_CALLS, LLM_LAT
from ..telemetry import get_tracer


class LLMWithMetrics:
    """
    Thin wrapper around `ChatOpenAI` that adds tracing and Prometheus metrics.

    Only `.invoke()` is used by the graph; all other attributes/methods are
    transparently proxied to the inner LLM instance.
    """

    def __init__(self, inner: ChatOpenAI, model: str) -> None:
        """
        Parameters
        ----------
        inner : ChatOpenAI
            The underlying LangChain LLM instance.
        model : str
            Model name (used for metrics labels).
        """
        self._inner = inner
        self._model = model
        self._tracer = get_tracer("llm")

    def invoke(self, messages: Sequence[Any]) -> Any:
        """
        Invoke the underlying LLM with tracing and latency/call metrics.

        Parameters
        ----------
        messages : Sequence[Any]
            LangChain-compatible message sequence.

        Returns
        -------
        Any
            The LLM response (typically an `AIMessage`).
        """
        status = "ok"
        t0 = time.perf_counter()
        with self._tracer.start_as_current_span(
            "llm.invoke",
            attributes={"llm.model": self._model},
        ):
            try:
                out = self._inner.invoke(messages)
            except Exception:
                status = "error"
                # record failure and re-raise
                LLM_CALLS.labels(self._model, status).inc()
                raise
        # observe latency and count
        LLM_LAT.labels(self._model).observe(time.perf_counter() - t0)
        LLM_CALLS.labels(self._model, status).inc()
        return out

    def __getattr__(self, name: str) -> Any:
        """
        Delegate unknown attribute/method access to the inner LLM.
        """
        return getattr(self._inner, name)


def build_llm() -> LLMWithMetrics:
    """
    Construct the traced/metricized LLM instance using settings.

    Returns
    -------
    LLMWithMetrics
        Wrapper around `ChatOpenAI` with tracing & Prometheus metrics.
    """
    model = settings.openai_model
    timeout = getattr(settings, "openai_timeout_sec", 30)
    base = ChatOpenAI(model=model, timeout=timeout)
    return LLMWithMetrics(base, model)
