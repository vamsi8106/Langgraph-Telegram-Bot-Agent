# # src/app/adapters/telegram_handlers.py
# import os, base64, logging, time
# from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
# from telegram import Update
# from telegram.ext import ContextTypes
# from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
# from openai import OpenAI

# from ..config.settings import settings
# from ..metrics import TG_UPDATES, GRAPH_LAT, observe
# from ..telemetry.otel import get_tracer
# from ..adapters.summarizer import summarize_window

# log = logging.getLogger(__name__)
# _tracer = get_tracer("handlers")

# # ---------- DI helpers ----------

# def _container_from_ctx(context: ContextTypes.DEFAULT_TYPE):
#     app = context.application
#     c = getattr(app, "bot_data", {}).get("container")
#     if not c:
#         c = getattr(app, "container", None)
#     if not c:
#         raise RuntimeError("DI container not found in application.bot_data['container']")
#     return c

# # ---------- Memory helpers ----------

# def _ensure_identity(container, update: Update):
#     u = update.effective_user
#     c = update.effective_chat
#     container.durable_mem.ensure_user(
#         user_id=u.id,
#         first_name=getattr(u, "first_name", None),
#         last_name=getattr(u, "last_name", None),
#         username=getattr(u, "username", None),
#     )
#     container.durable_mem.ensure_chat(
#         chat_id=c.id,
#         chat_type=c.type.value if hasattr(c.type, "value") else str(c.type),
#         title=getattr(c, "title", None),
#         user_id=u.id if (str(c.type) == "private") else None,
#     )

# def _build_context(container, chat_id: int, user_msg: str):
#     summary = container.durable_mem.get_summary(chat_id)
#     ctx = []
#     if summary:
#         ctx.append(SystemMessage(content=f"(summary) {summary}"))
#     window = container.short_mem.get_window(chat_id)
#     ctx.extend(window)
#     ctx.append(HumanMessage(content=user_msg))
#     return ctx

# def _after_reply(container, chat_id: int, user_msg: str, ai_msg: str):
#     # short-term window
#     container.short_mem.append_message(chat_id, HumanMessage(content=user_msg))
#     container.short_mem.append_message(chat_id, AIMessage(content=ai_msg))

#     # summarize if long
#     window = container.short_mem.get_window(chat_id, k=settings.window_size + 5)
#     if len(window) >= settings.window_size:
#         try:
#             summ = summarize_window(container.llm, window)
#             container.durable_mem.set_summary(chat_id, summ)
#             container.short_mem.clear(chat_id)
#             container.short_mem.append_message(chat_id, SystemMessage(content=f"(summary) {summ}"))
#         except Exception as e:
#             log.warning("Failed to summarize chat %s: %s", chat_id, e)

# def _persist_exchange(container, chat_id: int, user_text: str, ai_text: str):
#     container.durable_mem.add_message(chat_id=chat_id, role="user", content=user_text)
#     container.durable_mem.add_message(chat_id=chat_id, role="assistant", content=ai_text)

# # ---------- Graph wrapper ----------

# @retry(stop=stop_after_attempt(3),
#        wait=wait_exponential(multiplier=1, min=1, max=8),
#        retry=retry_if_exception_type(Exception),
#        reraise=True)
# def _graph_invoke_timed(graph, payload, thread_id: str) -> dict:
#     t0 = time.perf_counter()
#     with _tracer.start_as_current_span("graph.invoke"):
#         out = graph.invoke(payload, {"configurable": {"thread_id": thread_id}})
#     observe(GRAPH_LAT, time.perf_counter() - t0)
#     return out

# # ---------- Handlers ----------

# async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     TG_UPDATES.labels("start").inc()
#     await update.message.reply_text("Hey, I’m Karan. What should we chat about?")

# async def handle_text(graph, update: Update, context: ContextTypes.DEFAULT_TYPE):
#     TG_UPDATES.labels("text").inc()
#     c = _container_from_ctx(context)
#     chat_id = update.effective_chat.id
#     user_msg = update.message.text or ""
#     _ensure_identity(c, update)

#     full_ctx = _build_context(c, chat_id, user_msg)
#     out = _graph_invoke_timed(graph, {"messages": full_ctx}, thread_id=str(chat_id))

#     last = out.get("messages", [])[-1] if out.get("messages") else None
#     ai_text = getattr(last, "content", "") if last else ""
#     await _send_response(update, context, {
#         "response_type": out.get("response_type") or "text",
#         "messages": [AIMessage(content=ai_text)],
#         "audio_buffer": out.get("audio_buffer"),
#         "image_path": out.get("image_path"),
#     })

#     _persist_exchange(c, chat_id, user_msg, ai_text)
#     _after_reply(c, chat_id, user_msg, ai_text)

# async def handle_voice(graph, update: Update, context: ContextTypes.DEFAULT_TYPE):
#     TG_UPDATES.labels("voice").inc()
#     c = _container_from_ctx(context)
#     chat_id = update.effective_chat.id
#     _ensure_identity(c, update)

#     openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
#     v = update.message.voice
#     file = await context.bot.get_file(v.file_id)
#     p = "voice.ogg"
#     await file.download_to_drive(p)
#     try:
#         with open(p, "rb") as f:
#             tr = openai_client.audio.transcriptions.create(file=f, model="whisper-1")
#     finally:
#         try: os.remove(p)
#         except Exception: pass

#     user_msg = tr.text or ""
#     full_ctx = _build_context(c, chat_id, user_msg)
#     out = _graph_invoke_timed(graph, {"messages": full_ctx}, thread_id=str(chat_id))

#     last = out.get("messages", [])[-1] if out.get("messages") else None
#     ai_text = getattr(last, "content", "") if last else ""
#     await _send_response(update, context, {
#         "response_type": out.get("response_type") or "text",
#         "messages": [AIMessage(content=ai_text)],
#         "audio_buffer": out.get("audio_buffer"),
#         "image_path": out.get("image_path"),
#     })

#     _persist_exchange(c, chat_id, user_msg, ai_text)
#     _after_reply(c, chat_id, user_msg, ai_text)

# async def handle_photo(graph, update: Update, context: ContextTypes.DEFAULT_TYPE):
#     TG_UPDATES.labels("photo").inc()
#     c = _container_from_ctx(context)
#     chat_id = update.effective_chat.id
#     _ensure_identity(c, update)

#     openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
#     ph = update.message.photo[-1]
#     file = await context.bot.get_file(ph.file_id)
#     p = "image.jpg"
#     await file.download_to_drive(p)
#     try:
#         with open(p, "rb") as img:
#             b64 = base64.b64encode(img.read()).decode("utf-8")
#     finally:
#         try: os.remove(p)
#         except Exception: pass

#     vis = openai_client.chat.completions.create(
#         model=settings.openai_model,
#         messages=[{
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": "Describe the picture briefly."},
#                 {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
#             ],
#         }],
#     )
#     desc = (vis.choices[0].message.content or "").strip()
#     cap = update.message.caption or ""
#     user_msg = f"{cap} [IMAGE_ANALYSIS] {desc}".strip()

#     full_ctx = _build_context(c, chat_id, user_msg)
#     out = _graph_invoke_timed(graph, {"messages": full_ctx}, thread_id=str(chat_id))

#     last = out.get("messages", [])[-1] if out.get("messages") else None
#     ai_text = getattr(last, "content", "") if last else ""
#     await _send_response(update, context, {
#         "response_type": out.get("response_type") or "text",
#         "messages": [AIMessage(content=ai_text)],
#         "audio_buffer": out.get("audio_buffer"),
#         "image_path": out.get("image_path"),
#     })

#     _persist_exchange(c, chat_id, user_msg, ai_text)
#     _after_reply(c, chat_id, user_msg, ai_text)

# # ---------- response ----------

# async def _send_response(update: Update, context: ContextTypes.DEFAULT_TYPE, resp: dict):
#     t = resp.get("response_type") or "text"
#     last = resp.get("messages", [])[-1] if resp.get("messages") else None
#     content = getattr(last, "content", "") if last else ""

#     if t == "text":
#         await update.message.reply_text(content or "…")
#     elif t == "audio":
#         audio = resp.get("audio_buffer")
#         if audio:
#             await update.message.reply_voice(voice=audio)
#         else:
#             await update.message.reply_text("Audio not available.")
#     elif t == "image":
#         path = resp.get("image_path")
#         if path and os.path.exists(path):
#             with open(path, "rb") as f:
#                 await update.message.reply_photo(photo=f)
#         else:
#             await update.message.reply_text("Image not available.")
#     else:
#         await update.message.reply_text(content or "Something felt off.")


# src/app/adapters/telegram_handlers.py
from __future__ import annotations

import base64
import logging
import os
import time
from typing import Any, Dict, Optional

from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from telegram import Update
from telegram.ext import ContextTypes
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..config.settings import settings
from ..metrics import GRAPH_LAT, TG_UPDATES, observe
from ..telemetry import get_tracer
from ..adapters.summarizer import summarize_window

log = logging.getLogger(__name__)
_tracer = get_tracer("handlers")


# ---------- DI helpers ----------

def _container_from_ctx(context: ContextTypes.DEFAULT_TYPE):
    """
    Fetch the DI container stored on the application instance.
    """
    app = context.application
    c = getattr(app, "bot_data", {}).get("container")
    if not c:
        c = getattr(app, "container", None)
    if not c:
        raise RuntimeError("DI container not found in application.bot_data['container']")
    return c


# ---------- Memory helpers ----------

def _ensure_identity(container, update: Update) -> None:
    """
    Upsert user/chat identity in the durable store.
    """
    u = update.effective_user
    c = update.effective_chat
    container.durable_mem.ensure_user(
        user_id=u.id,
        first_name=getattr(u, "first_name", None),
        last_name=getattr(u, "last_name", None),
        username=getattr(u, "username", None),
    )
    container.durable_mem.ensure_chat(
        chat_id=c.id,
        chat_type=c.type.value if hasattr(c.type, "value") else str(c.type),
        title=getattr(c, "title", None),
        user_id=u.id if (str(c.type) == "private") else None,
    )


def _build_context(container, chat_id: int, user_msg: str) -> list:
    """
    Build model context: (summary?) + rolling window + current user message.
    """
    ctx: list = []
    summary = container.durable_mem.get_summary(chat_id)
    if summary:
        ctx.append(SystemMessage(content=f"(summary) {summary}"))
    window = container.short_mem.get_window(chat_id)
    ctx.extend(window)
    ctx.append(HumanMessage(content=user_msg))
    return ctx


def _after_reply(container, chat_id: int, user_msg: str, ai_msg: str) -> None:
    """
    Append new turn to short-term memory and summarize if the window is long.
    """
    # Short-term window
    container.short_mem.append_message(chat_id, HumanMessage(content=user_msg))
    container.short_mem.append_message(chat_id, AIMessage(content=ai_msg))

    # Summarize if long
    window = container.short_mem.get_window(chat_id, k=settings.window_size + 5)
    if len(window) >= settings.window_size:
        try:
            summ = summarize_window(container.llm, window)
            container.durable_mem.set_summary(chat_id, summ)
            container.short_mem.clear(chat_id)
            container.short_mem.append_message(chat_id, SystemMessage(content=f"(summary) {summ}"))
        except Exception as e:  # pragma: no cover (best-effort summary)
            log.warning("Failed to summarize chat %s: %s", chat_id, e)


def _persist_exchange(container, chat_id: int, user_text: str, ai_text: str) -> None:
    """
    Persist the user/assistant messages to durable storage.
    """
    container.durable_mem.add_message(chat_id=chat_id, role="user", content=user_text)
    container.durable_mem.add_message(chat_id=chat_id, role="assistant", content=ai_text)


# ---------- Graph wrapper ----------

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _graph_invoke_timed(graph, payload: Dict[str, Any], thread_id: str) -> Dict[str, Any]:
    """
    Invoke the graph with timing metrics and OpenTelemetry span.

    Retries transient failures (up to 3) with exponential backoff.
    """
    t0 = time.perf_counter()
    with _tracer.start_as_current_span("graph.invoke", attributes={"thread_id": thread_id}):
        out = graph.invoke(payload, {"configurable": {"thread_id": thread_id}})
    observe(GRAPH_LAT, time.perf_counter() - t0)
    return out


# ---------- Handlers ----------

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /start: basic greeting.
    """
    TG_UPDATES.labels("start").inc()
    await update.message.reply_text("Hey, I’m Karan. What should we chat about?")


async def handle_text(graph, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle plain text messages.
    """
    TG_UPDATES.labels("text").inc()
    c = _container_from_ctx(context)
    chat_id = update.effective_chat.id
    user_msg = update.message.text or ""
    _ensure_identity(c, update)

    full_ctx = _build_context(c, chat_id, user_msg)
    out = _graph_invoke_timed(graph, {"messages": full_ctx}, thread_id=str(chat_id))

    last = out.get("messages", [])[-1] if out.get("messages") else None
    ai_text = getattr(last, "content", "") if last else ""
    await _send_response(
        update,
        context,
        {
            "response_type": out.get("response_type") or "text",
            "messages": [AIMessage(content=ai_text)],
            "audio_buffer": out.get("audio_buffer"),
            "image_path": out.get("image_path"),
        },
    )

    _persist_exchange(c, chat_id, user_msg, ai_text)
    _after_reply(c, chat_id, user_msg, ai_text)


async def handle_voice(graph, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle voice note: transcribe with Whisper, then pass text to the graph.
    """
    TG_UPDATES.labels("voice").inc()
    c = _container_from_ctx(context)
    chat_id = update.effective_chat.id
    _ensure_identity(c, update)

    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    v = update.message.voice
    file = await context.bot.get_file(v.file_id)
    p = "voice.ogg"
    await file.download_to_drive(p)
    try:
        with open(p, "rb") as f:
            tr = openai_client.audio.transcriptions.create(file=f, model="whisper-1")
    finally:
        try:
            os.remove(p)
        except Exception:  # pragma: no cover
            pass

    user_msg = tr.text or ""
    full_ctx = _build_context(c, chat_id, user_msg)
    out = _graph_invoke_timed(graph, {"messages": full_ctx}, thread_id=str(chat_id))

    last = out.get("messages", [])[-1] if out.get("messages") else None
    ai_text = getattr(last, "content", "") if last else ""
    await _send_response(
        update,
        context,
        {
            "response_type": out.get("response_type") or "text",
            "messages": [AIMessage(content=ai_text)],
            "audio_buffer": out.get("audio_buffer"),
            "image_path": out.get("image_path"),
        },
    )

    _persist_exchange(c, chat_id, user_msg, ai_text)
    _after_reply(c, chat_id, user_msg, ai_text)


async def handle_photo(graph, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle photo: briefly describe via vision call, append caption, then run graph.
    """
    TG_UPDATES.labels("photo").inc()
    c = _container_from_ctx(context)
    chat_id = update.effective_chat.id
    _ensure_identity(c, update)

    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    ph = update.message.photo[-1]
    file = await context.bot.get_file(ph.file_id)
    p = "image.jpg"
    await file.download_to_drive(p)
    try:
        with open(p, "rb") as img:
            b64 = base64.b64encode(img.read()).decode("utf-8")
    finally:
        try:
            os.remove(p)
        except Exception:  # pragma: no cover
            pass

    vis = openai_client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe the picture briefly."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }
        ],
    )
    desc = (vis.choices[0].message.content or "").strip()
    cap = update.message.caption or ""
    user_msg = f"{cap} [IMAGE_ANALYSIS] {desc}".strip()

    full_ctx = _build_context(c, chat_id, user_msg)
    out = _graph_invoke_timed(graph, {"messages": full_ctx}, thread_id=str(chat_id))

    last = out.get("messages", [])[-1] if out.get("messages") else None
    ai_text = getattr(last, "content", "") if last else ""
    await _send_response(
        update,
        context,
        {
            "response_type": out.get("response_type") or "text",
            "messages": [AIMessage(content=ai_text)],
            "audio_buffer": out.get("audio_buffer"),
            "image_path": out.get("image_path"),
        },
    )

    _persist_exchange(c, chat_id, user_msg, ai_text)
    _after_reply(c, chat_id, user_msg, ai_text)


# ---------- response ----------

async def _send_response(update: Update, context: ContextTypes.DEFAULT_TYPE, resp: Dict[str, Any]) -> None:
    """
    Send the appropriate response type to Telegram based on the graph output.
    """
    t = resp.get("response_type") or "text"
    last = resp.get("messages", [])[-1] if resp.get("messages") else None
    content = getattr(last, "content", "") if last else ""

    if t == "text":
        await update.message.reply_text(content or "…")
    elif t == "audio":
        audio = resp.get("audio_buffer")
        if audio:
            await update.message.reply_voice(voice=audio)
        else:
            await update.message.reply_text("Audio not available.")
    elif t == "image":
        path = resp.get("image_path")
        if path and os.path.exists(path):
            with open(path, "rb") as f:
                await update.message.reply_photo(photo=f)
        else:
            await update.message.reply_text("Image not available.")
    else:
        await update.message.reply_text(content or "Something felt off.")
