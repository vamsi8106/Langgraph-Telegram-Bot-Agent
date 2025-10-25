# import json, redis, hashlib
# from typing import List, Optional
# from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
# from ..config.settings import settings

# def _sha256(s: str) -> str:
#     return hashlib.sha256(s.encode("utf-8")).hexdigest()

# class RedisMemoryStore:
#     def __init__(self):
#         # Chat window (short-term) stays in DB 0 (or your default)
#         self.r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)
#         self.ttl = settings.redis_ttl_seconds
#         self.window = settings.window_size

#         # ===== “cache/qa” folder =====
#         # Use a separate DB for all cache keys — cleaner separation.
#         self.r_cache = redis.Redis(
#             host=settings.redis_host,
#             port=settings.redis_port,
#             db=settings.redis_cache_db,
#         )
#         self.qa_enabled = settings.qa_cache_enabled
#         self.qa_ttl = settings.qa_cache_ttl_seconds
#         # Namespace == “folder path” → cache:qa:<hash>
#         self.qa_ns = settings.qa_cache_namespace.rstrip(":")
#         self.qa_min = settings.qa_cache_min_chars
#         self.qa_inc_sys = settings.qa_cache_include_system_prompt

#     # --------- short-term convo window ----------
#     def _k(self, chat_id: int): 
#         return f"karan:chat:{chat_id}:window"

#     def append_message(self, chat_id: int, msg: BaseMessage) -> None:
#         payload = {"type": msg.type, "content": msg.content}
#         self.r.lpush(self._k(chat_id), json.dumps(payload))
#         self.r.ltrim(self._k(chat_id), 0, self.window - 1)
#         self.r.expire(self._k(chat_id), self.ttl)

#     def get_window(self, chat_id: int, k: int | None = None) -> List[BaseMessage]:
#         k = k or self.window
#         raw = self.r.lrange(self._k(chat_id), 0, k - 1)[::-1]
#         out: List[BaseMessage] = []
#         for b in raw:
#             p = json.loads(b)
#             t, c = p.get("type"), p.get("content", "")
#             out.append(
#                 HumanMessage(content=c) if t == "human" else
#                 AIMessage(content=c) if t == "ai" else
#                 SystemMessage(content=c)
#             )
#         return out

#     def clear(self, chat_id: int) -> None:
#         self.r.delete(self._k(chat_id))

#     # --------- Q&A cache inside “cache/qa” ---------
#     def _qa_key(self, *, model: str, system_prompt: Optional[str], last_user_text: str) -> str:
#         base = model.strip()
#         u = last_user_text.strip().lower()
#         parts = [base, u]
#         if self.qa_inc_sys and system_prompt:
#             parts.append(system_prompt.strip())
#         raw = "||".join(parts)
#         return f"{self.qa_ns}:{_sha256(raw)}"   # e.g., cache:qa:1a2b3c...

#     def qa_get(self, *, model: str, system_prompt: Optional[str], last_user_text: str) -> Optional[str]:
#         if not self.qa_enabled or len(last_user_text.strip()) < self.qa_min:
#             return None
#         key = self._qa_key(model=model, system_prompt=system_prompt, last_user_text=last_user_text)
#         val = self.r_cache.get(key)
#         return val.decode("utf-8") if val else None

#     def qa_set(self, *, model: str, system_prompt: Optional[str], last_user_text: str, answer: str) -> None:
#         if not self.qa_enabled or len(last_user_text.strip()) < self.qa_min:
#             return
#         key = self._qa_key(model=model, system_prompt=system_prompt, last_user_text=last_user_text)
#         self.r_cache.setex(key, self.qa_ttl, answer)

#     # Handy maintenance helpers (optional):
#     def qa_del(self, *, model: str, system_prompt: Optional[str], last_user_text: str) -> int:
#         """Delete a single cached answer; returns #deleted (0/1)."""
#         key = self._qa_key(model=model, system_prompt=system_prompt, last_user_text=last_user_text)
#         return self.r_cache.delete(key)

#     def qa_clear_all(self) -> int:
#         """Delete ALL keys in the cache:qa “folder”. Returns count deleted."""
#         pattern = f"{self.qa_ns}:*"
#         pipe = self.r_cache.pipeline()
#         n = 0
#         for k in self.r_cache.scan_iter(match=pattern, count=1000):
#             pipe.delete(k)
#             n += 1
#         if n:
#             pipe.execute()
#         return n

#     def qa_list_keys(self, limit: int = 50) -> list[str]:
#         """List some keys in cache:qa for inspection."""
#         out = []
#         for i, k in enumerate(self.r_cache.scan_iter(match=f"{self.qa_ns}:*", count=1000)):
#             out.append(k.decode("utf-8"))
#             if i + 1 >= limit:
#                 break
#         return out

# src/app/adapters/memory_redis.py
from __future__ import annotations

import hashlib
import json
from typing import List, Optional

import redis
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from ..config.settings import settings


def _sha256(s: str) -> str:
    """Return a hex SHA-256 hash for the input string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class RedisMemoryStore:
    """
    Short-term chat memory + global Q&A cache backed by Redis.

    - Conversation window is stored in Redis DB 0 under:
      `karan:chat:{chat_id}:window`
    - Q&A cache lives in a separate Redis DB (settings.redis_cache_db),
      with a “folder-like” namespace: `cache:qa:<hash>`.
    """

    def __init__(self) -> None:
        # --- Chat window (short-term) ---
        self.r = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=0,
        )
        self.ttl = settings.redis_ttl_seconds
        self.window = settings.window_size

        # --- “cache/qa” folder (separate DB) ---
        self.r_cache = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_cache_db,
        )
        self.qa_enabled = settings.qa_cache_enabled
        self.qa_ttl = settings.qa_cache_ttl_seconds
        self.qa_ns = settings.qa_cache_namespace.rstrip(":")  # e.g., "cache:qa"
        self.qa_min = settings.qa_cache_min_chars
        self.qa_inc_sys = settings.qa_cache_include_system_prompt

    # ---------------- Conversation window ----------------

    def _k(self, chat_id: int) -> str:
        """Return Redis key for the chat’s rolling window."""
        return f"karan:chat:{chat_id}:window"

    def append_message(self, chat_id: int, msg: BaseMessage) -> None:
        """
        Append a single message to the rolling window, trim, and set TTL.

        Parameters
        ----------
        chat_id : int
            Chat identifier.
        msg : BaseMessage
            LangChain message (`HumanMessage`, `AIMessage`, or `SystemMessage`).
        """
        payload = {"type": msg.type, "content": msg.content}
        key = self._k(chat_id)
        self.r.lpush(key, json.dumps(payload))
        self.r.ltrim(key, 0, self.window - 1)
        self.r.expire(key, self.ttl)

    def get_window(self, chat_id: int, k: Optional[int] = None) -> List[BaseMessage]:
        """
        Read the last `k` messages from the window (default = configured size).

        Parameters
        ----------
        chat_id : int
            Chat identifier.
        k : Optional[int]
            Number of messages to fetch (newest first). Defaults to window size.

        Returns
        -------
        List[BaseMessage]
            Messages in chronological order (oldest → newest).
        """
        key = self._k(chat_id)
        limit = k or self.window
        raw = self.r.lrange(key, 0, limit - 1)[::-1]

        out: List[BaseMessage] = []
        for b in raw:
            p = json.loads(b)
            t, c = p.get("type"), p.get("content", "")
            out.append(
                HumanMessage(content=c) if t == "human"
                else AIMessage(content=c) if t == "ai"
                else SystemMessage(content=c)
            )
        return out

    def clear(self, chat_id: int) -> None:
        """
        Delete the chat’s window entirely.
        """
        self.r.delete(self._k(chat_id))

    # ---------------- Q&A cache (cache/qa/*) ----------------

    def _qa_key(self, *, model: str, system_prompt: Optional[str], last_user_text: str) -> str:
        """
        Build a stable key for the global Q&A cache.

        Key shape: `cache:qa:<sha256(model||user_text||system_prompt?)>`
        """
        base = model.strip()
        u = last_user_text.strip().lower()
        parts = [base, u]
        if self.qa_inc_sys and system_prompt:
            parts.append(system_prompt.strip())
        raw = "||".join(parts)
        return f"{self.qa_ns}:{_sha256(raw)}"  # e.g., cache:qa:1a2b3c...

    def qa_get(self, *, model: str, system_prompt: Optional[str], last_user_text: str) -> Optional[str]:
        """
        Fetch a cached answer for the last user text (exact match).

        Returns
        -------
        Optional[str]
            Cached answer if present and cache is enabled; else None.
        """
        if not self.qa_enabled or len(last_user_text.strip()) < self.qa_min:
            return None
        key = self._qa_key(model=model, system_prompt=system_prompt, last_user_text=last_user_text)
        val = self.r_cache.get(key)
        return val.decode("utf-8") if val else None

    def qa_set(self, *, model: str, system_prompt: Optional[str], last_user_text: str, answer: str) -> None:
        """
        Store an answer for the last user text with TTL.
        """
        if not self.qa_enabled or len(last_user_text.strip()) < self.qa_min:
            return
        key = self._qa_key(model=model, system_prompt=system_prompt, last_user_text=last_user_text)
        self.r_cache.setex(key, self.qa_ttl, answer)

    # ---------------- Maintenance helpers ----------------

    def qa_del(self, *, model: str, system_prompt: Optional[str], last_user_text: str) -> int:
        """
        Delete a single cached entry.

        Returns
        -------
        int
            Number of keys deleted (0 or 1).
        """
        key = self._qa_key(model=model, system_prompt=system_prompt, last_user_text=last_user_text)
        return int(self.r_cache.delete(key) or 0)

    def qa_clear_all(self) -> int:
        """
        Delete all keys in the cache:qa “folder”.

        Returns
        -------
        int
            Count of deleted keys.
        """
        pattern = f"{self.qa_ns}:*"
        pipe = self.r_cache.pipeline()
        n = 0
        for k in self.r_cache.scan_iter(match=pattern, count=1000):
            pipe.delete(k)
            n += 1
        if n:
            pipe.execute()
        return n

    def qa_list_keys(self, limit: int = 50) -> List[str]:
        """
        List some keys in cache:qa for inspection.

        Parameters
        ----------
        limit : int
            Maximum number of keys to return.

        Returns
        -------
        List[str]
            Key names (UTF-8 strings).
        """
        out: List[str] = []
        for i, k in enumerate(self.r_cache.scan_iter(match=f"{self.qa_ns}:*", count=1000)):
            out.append(k.decode("utf-8"))
            if i + 1 >= limit:
                break
        return out
