
# import logging, random, os, sqlite3
# from typing import Optional
# from langgraph.graph import StateGraph, START, END, MessagesState
# from langgraph.checkpoint.sqlite import SqliteSaver
# from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
# from ..constants import SYSTEM_PROMPT
# from ..config.settings import settings

# log = logging.getLogger(__name__)

# class KaranState(MessagesState):
#     response_type: Optional[str] = None
#     audio_buffer: Optional[bytes] = None
#     image_path: Optional[str] = None

# def _router_node(container):
#     def _fn(state: KaranState):
#         msgs = state.get("messages", [])
#         last = msgs[-1] if msgs else None
#         text = (getattr(last, "content", "") or "").lower()

#         if any(w in text for w in ["pic", "photo", "selfie", "image", "picture"]):
#             rt = "image"
#         elif any(w in text for w in ["voice", "audio", "hear", "voice note"]):
#             rt = "audio"
#         else:
#             rt = "audio" if random.random() > 0.9 else "text"

#         return {"response_type": rt}
#     return _fn

# def _extract_last_user_text(msgs) -> str:
#     # last HumanMessage content (fallback: empty)
#     for m in reversed(msgs):
#         if isinstance(m, HumanMessage) and m.content:
#             return str(m.content)
#     return ""

# def _maybe_get_system_summary(msgs) -> Optional[str]:
#     # If your handlers prepend a (summary) SystemMessage, include it in cache key (optional)
#     for m in msgs:
#         if isinstance(m, SystemMessage) and isinstance(m.content, str) and m.content.startswith("(summary)"):
#             return m.content
#     return None

# def _text_node(container):
#     def _fn(state: KaranState):
#         msgs = state.get("messages", [])
#         sys = SystemMessage(content=SYSTEM_PROMPT)
#         convo = [sys] + msgs

#         # ---- Q&A cache (global exact-match) ----
#         last_user = _extract_last_user_text(msgs)
#         system_for_key = SYSTEM_PROMPT if settings.qa_cache_include_system_prompt else None
#         # Optionally also include summary line to isolate answers by context:
#         summary_line = _maybe_get_system_summary(msgs)
#         if summary_line and settings.qa_cache_include_system_prompt:
#             system_for_key = f"{SYSTEM_PROMPT}\n{summary_line}"

#         cached = container.short_mem.qa_get(
#             model=settings.openai_model,
#             system_prompt=system_for_key,
#             last_user_text=last_user
#         )
#         if cached:
#             ai = AIMessage(content=cached)
#             return {"messages": [ai]}

#         # ---- No cache hit → call LLM ----
#         ai = container.llm.invoke(convo)
#         if not isinstance(ai, AIMessage):
#             ai = AIMessage(content=str(ai))

#         # ---- Store in cache ----
#         container.short_mem.qa_set(
#             model=settings.openai_model,
#             system_prompt=system_for_key,
#             last_user_text=last_user,
#             answer=ai.content or ""
#         )
#         return {"messages": [ai]}
#     return _fn

# def _final_node(container):
#     basic_img_prompt = (
#         "Create a realistic image of Karan: male, late 20s/early 30s, medium brown skin, "
#         "neatly trimmed beard, short black hair, black rectangular glasses, black long-sleeve crew-neck shirt. "
#         "Background: blurred tech conference with developers around."
#     )
#     def _fn(state: KaranState):
#         rt = state.get("response_type") or "text"
#         if rt == "audio":
#             content = ""
#             for m in reversed(state.get("messages", [])):
#                 if isinstance(m, AIMessage) and m.content:
#                     content = m.content
#                     break
#             if not content and state.get("messages"):
#                 content = getattr(state["messages"][-1], "content", "")
#             audio = container.tts(content or "Hi, this is Karan.")
#             return {"audio_buffer": audio}
#         if rt == "image":
#             path = container.image_gen(basic_img_prompt)
#             return {"image_path": path}
#         return {}
#     return _fn

# DB_URL = os.getenv("SHORT_TERM_DB_URL", "short_term_memory.db")

# def build_graph(container, attach_conn_for_tests: bool = False):
#     use_uri = DB_URL.startswith("file:")
#     conn = sqlite3.connect(DB_URL, check_same_thread=False, uri=use_uri)
#     checkpointer = SqliteSaver(conn)

#     sg = StateGraph(KaranState)
#     sg.add_node("router", _router_node(container))
#     sg.add_node("text", _text_node(container))
#     sg.add_node("final", _final_node(container))

#     sg.add_edge(START, "router")
#     sg.add_edge("router", "text")
#     sg.add_edge("text", "final")
#     sg.add_edge("final", END)

#     graph = sg.compile(checkpointer=checkpointer)

#     if attach_conn_for_tests:
#         setattr(graph, "_conn", conn)

#     log.info("Graph compiled.")
#     return graph


# src/app/workflows/karan_graph.py
"""
Karan bot LangGraph workflow.

Pipeline:
1) router  -> decide response_type ("text" | "audio" | "image")
2) text    -> build prompt + (optional) Redis Q&A cache; invoke LLM
3) final   -> materialize audio/image if requested

Checkpoints:
- Uses SQLite checkpointer for graph state; separate from Redis/Postgres.
"""

from __future__ import annotations

import logging
import os
import random
import sqlite3
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, MessagesState, StateGraph

from ..config.settings import settings
from ..constants import SYSTEM_PROMPT

log = logging.getLogger(__name__)


class KaranState(MessagesState):
    """
    LangGraph state with optional materialized outputs.
    """
    response_type: Optional[str] = None
    audio_buffer: Optional[bytes] = None
    image_path: Optional[str] = None


# ---------- Router ----------

def _router_node(container):
    """
    Heuristic router that sets response_type based on user text.
    """
    def _fn(state: KaranState):
        msgs = state.get("messages", [])
        last = msgs[-1] if msgs else None
        text = (getattr(last, "content", "") or "").lower()

        if any(w in text for w in ["pic", "photo", "selfie", "image", "picture"]):
            rt = "image"
        elif any(w in text for w in ["voice", "audio", "hear", "voice note"]):
            rt = "audio"
        else:
            # Mostly text; randomly return audio sometimes to add variety.
            rt = "audio" if random.random() > 0.9 else "text"

        return {"response_type": rt}
    return _fn


# ---------- Helpers for cache key composition ----------

def _extract_last_user_text(msgs) -> str:
    """
    Return last HumanMessage content (or empty string).
    """
    for m in reversed(msgs):
        if isinstance(m, HumanMessage) and m.content:
            return str(m.content)
    return ""


def _maybe_get_system_summary(msgs) -> Optional[str]:
    """
    If handlers injected a (summary) SystemMessage, return its content.
    """
    for m in msgs:
        if isinstance(m, SystemMessage) and isinstance(m.content, str) and m.content.startswith("(summary)"):
            return m.content
    return None


# ---------- Text node (LLM + Q&A cache) ----------

def _text_node(container):
    """
    Build prompt, attempt a Redis Q&A cache read, otherwise call LLM and cache.
    """
    def _fn(state: KaranState):
        msgs = state.get("messages", [])
        sys = SystemMessage(content=SYSTEM_PROMPT)
        convo = [sys] + msgs

        # ---- Q&A cache (global exact-match) ----
        last_user = _extract_last_user_text(msgs)
        system_for_key = SYSTEM_PROMPT if settings.qa_cache_include_system_prompt else None

        # Optionally include the persisted summary in the cache key to avoid
        # cross-context leakage when chats diverge significantly.
        summary_line = _maybe_get_system_summary(msgs)
        if summary_line and settings.qa_cache_include_system_prompt:
            system_for_key = f"{SYSTEM_PROMPT}\n{summary_line}"

        cached = container.short_mem.qa_get(
            model=settings.openai_model,
            system_prompt=system_for_key,
            last_user_text=last_user,
        )
        if cached:
            ai = AIMessage(content=cached)
            return {"messages": [ai]}

        # ---- No cache hit → call LLM ----
        ai = container.llm.invoke(convo)
        if not isinstance(ai, AIMessage):
            ai = AIMessage(content=str(ai))

        # ---- Store in cache ----
        container.short_mem.qa_set(
            model=settings.openai_model,
            system_prompt=system_for_key,
            last_user_text=last_user,
            answer=ai.content or "",
        )
        return {"messages": [ai]}
    return _fn


# ---------- Final node (materialize side-effects) ----------

def _final_node(container):
    """
    Materialize audio/image outputs based on response_type.
    """
    basic_img_prompt = (
        "Create a realistic image of Karan: male, late 20s/early 30s, medium brown skin, "
        "neatly trimmed beard, short black hair, black rectangular glasses, black long-sleeve crew-neck shirt. "
        "Background: blurred tech conference with developers around."
    )

    def _fn(state: KaranState):
        rt = state.get("response_type") or "text"

        if rt == "audio":
            # Use the last AI message content as the narration text.
            content = ""
            for m in reversed(state.get("messages", [])):
                if isinstance(m, AIMessage) and m.content:
                    content = m.content
                    break
            if not content and state.get("messages"):
                content = getattr(state["messages"][-1], "content", "")
            audio = container.tts(content or "Hi, this is Karan.")
            return {"audio_buffer": audio}

        if rt == "image":
            path = container.image_gen(basic_img_prompt)
            return {"image_path": path}

        # Default: text response already in messages.
        return {}
    return _fn


# ---------- Graph builder ----------

DB_URL = os.getenv("SHORT_TERM_DB_URL", "short_term_memory.db")


def build_graph(container, attach_conn_for_tests: bool = False):
    """
    Compile the LangGraph with a SQLite checkpointer.

    Parameters
    ----------
    container : Any
        DI container providing .llm, .tts, .image_gen, .short_mem, etc.
    attach_conn_for_tests : bool
        If True, attach the sqlite3 connection to graph as `_conn` (tests).

    Returns
    -------
    RunnableGraph
        A compiled graph ready for .invoke(payload, config) calls.
    """
    use_uri = DB_URL.startswith("file:")
    conn = sqlite3.connect(DB_URL, check_same_thread=False, uri=use_uri)
    checkpointer = SqliteSaver(conn)

    sg = StateGraph(KaranState)
    sg.add_node("router", _router_node(container))
    sg.add_node("text", _text_node(container))
    sg.add_node("final", _final_node(container))

    sg.add_edge(START, "router")
    sg.add_edge("router", "text")
    sg.add_edge("text", "final")
    sg.add_edge("final", END)

    graph = sg.compile(checkpointer=checkpointer)

    if attach_conn_for_tests:
        setattr(graph, "_conn", conn)  # expose for test cleanup

    log.info("Graph compiled.")
    return graph
