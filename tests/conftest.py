# tests/conftest.py
import os
import pytest
from dataclasses import dataclass
from typing import Any, List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from app.workflows.karan_graph import build_graph


# ---- Dummy components (no network) ----

class DummyLLM:
    def invoke(self, messages):
        # Minimal echo; real content not important for tests
        return AIMessage(content="ok from dummy llm")


def dummy_tts(text: str) -> bytes:
    return b"voice-bytes"


def dummy_image_gen(prompt: str, size: str = "1024x1024") -> str:
    return "fake.png"


class ShortMemFake:
    """In-memory short-term window + QA cache for tests (no Redis)."""
    def __init__(self):
        self._windows = {}
        self._cache = {}

    def append_message(self, chat_id: int, msg: BaseMessage) -> None:
        self._windows.setdefault(chat_id, []).append(msg)

    def get_window(self, chat_id: int, k: int = 30) -> List[BaseMessage]:
        w = self._windows.get(chat_id, [])
        return w[-k:]

    def clear(self, chat_id: int) -> None:
        self._windows.pop(chat_id, None)

    # QA cache
    def qa_get(self, *, model: str, system_prompt: Optional[str], last_user_text: str) -> Optional[str]:
        key = (model, system_prompt or "", last_user_text.strip().lower())
        return self._cache.get(key)

    def qa_set(self, *, model: str, system_prompt: Optional[str], last_user_text: str, answer: str) -> None:
        key = (model, system_prompt or "", last_user_text.strip().lower())
        self._cache[key] = answer


class DurableMemFake:
    """In-memory durable memory for tests (no Postgres)."""
    def __init__(self):
        self._summary = {}
        self._messages = []

    def ensure_user(self, **kwargs):  # pragma: no cover - not used in unit tests
        pass

    def ensure_chat(self, **kwargs):  # pragma: no cover - not used in unit tests
        pass

    def set_summary(self, chat_id: int, text: str) -> None:
        self._summary[chat_id] = text

    def get_summary(self, chat_id: int) -> Optional[str]:
        return self._summary.get(chat_id)

    def add_message(self, *, chat_id: int, role: str, content: str) -> None:
        self._messages.append((chat_id, role, content))

    def add_messages_bulk(self, *, chat_id: int, turns):  # pragma: no cover
        for r, c in turns:
            self.add_message(chat_id=chat_id, role=r, content=c)


@dataclass
class TestContainer:
    llm: Any
    vector: Any
    tts: Any
    image_gen: Any
    short_mem: Any
    durable_mem: Any


@pytest.fixture(autouse=True)
def _test_env(monkeypatch, tmp_path):
    # lightweight test env; avoid real services
    monkeypatch.setenv("ENV", "test")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("LOGS_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("APP_LOG_FILE", str(tmp_path / "logs/app.log"))
    # in-memory sqlite for LangGraph checkpointer
    monkeypatch.setenv("SHORT_TERM_DB_URL", "file::memory:?cache=shared")
    # set fake keys to satisfy any client constructors in adapters (when used)
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test")
    yield


@pytest.fixture
def container() -> TestContainer:
    return TestContainer(
        llm=DummyLLM(),
        vector=None,
        tts=dummy_tts,
        image_gen=dummy_image_gen,
        short_mem=ShortMemFake(),
        durable_mem=DurableMemFake(),
    )


@pytest.fixture
def graph(container):
    g = build_graph(container, attach_conn_for_tests=True)
    try:
        yield g
    finally:
        conn = getattr(g, "_conn", None)
        if conn:
            conn.close()
