# src/app/entrypoints/telegram_bot.py
from __future__ import annotations

import logging
import time
from typing import Any, Callable

from dotenv import load_dotenv
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ..adapters.telegram_handlers import (
    handle_photo,
    handle_start,
    handle_text,
    handle_voice,
)
from ..config.logging import configure_logging
from ..config.settings import settings
from ..di import build_container
from ..metrics import HANDLER_LAT, TG_UPDATES, inc, observe
from ..telemetry import init_telemetry
from ..workflows.karan_graph import build_graph

# Load environment variables as early as possible.
load_dotenv()

log = logging.getLogger("app.telegram")


async def log_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Global error handler: log uncaught exceptions from handlers.
    """
    log.exception("Unhandled error", exc_info=context.error)


# ---------- metrics-aware wrappers (async-safe) ----------

def _wrap_simple(name: str, fn: Callable[..., Any]):
    """
    Wrap a simple handler with Prometheus timing + count.
    """
    async def _inner(update: "Update", context: ContextTypes.DEFAULT_TYPE):
        inc(TG_UPDATES, type=name)
        t0 = time.perf_counter()
        try:
            return await fn(update, context)
        finally:
            observe(HANDLER_LAT, time.perf_counter() - t0, handler=name)

    return _inner


def _wrap_with_graph(name: str, fn: Callable[..., Any], graph: Any):
    """
    Wrap a graph-dependent handler with Prometheus timing + count.
    """
    async def _inner(update: "Update", context: ContextTypes.DEFAULT_TYPE):
        inc(TG_UPDATES, type=name)
        t0 = time.perf_counter()
        try:
            return await fn(graph, update, context)
        finally:
            observe(HANDLER_LAT, time.perf_counter() - t0, handler=name)

    return _inner


# --------------------------------------------------------

def build_app(graph: Any) -> Application:
    """
    Configure the Telegram application with handlers and error hooks.

    Parameters
    ----------
    graph : Any
        The compiled LangGraph instance.

    Returns
    -------
    Application
        A fully configured python-telegram-bot Application.
    """
    app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # /start (no graph needed)
    app.add_handler(CommandHandler("start", _wrap_simple("start", handle_start)))

    # text / voice / photo (need graph)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, _wrap_with_graph("text", handle_text, graph))
    )
    app.add_handler(MessageHandler(filters.VOICE, _wrap_with_graph("voice", handle_voice, graph)))
    app.add_handler(MessageHandler(filters.PHOTO, _wrap_with_graph("photo", handle_photo, graph)))

    app.add_error_handler(log_error)
    return app


def main() -> None:
    """
    Entry point: configure logging/telemetry, build DI + graph, and start polling.

    Notes
    -----
    This function is synchronous by design. `Application.run_polling()` manages
    the asyncio event loop internally (PTB v20+).
    """
    # Configure logging & telemetry (Prometheus + tracing if enabled)
    configure_logging()
    init_telemetry()
    log.info("env=%s debug=%s", settings.env, settings.debug)

    # Build DI container and graph
    container = build_container()
    graph = build_graph(container)

    # Expose container to handlers via bot_data
    app = build_app(graph)
    app.bot_data["container"] = container

    log.info("Starting Telegram polling")
    app.run_polling(allowed_updates=["message"])  # blocking call

if __name__ == "__main__":
    main()
