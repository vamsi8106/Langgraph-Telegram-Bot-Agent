import types
import pytest
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.adapters import telegram_handlers as th

class ShortMemFake:
    def __init__(self): self.w = {}; self.ops=[]
    def append_message(self, chat_id, msg):
        self.w.setdefault(chat_id, []).append(msg)
    def get_window(self, chat_id, k=30):
        return list(self.w.get(chat_id, []))[-k:]
    def clear(self, chat_id): self.ops.append(("clear", chat_id)); self.w.pop(chat_id, None)

class DurableMemFake:
    def __init__(self): self.summ={}; self.ops=[]
    def ensure_user(self, **kw): pass
    def ensure_chat(self, **kw): pass
    def set_summary(self, chat_id, text): self.summ[chat_id]=text; self.ops.append(("set_summary", chat_id, text))
    def get_summary(self, chat_id): return self.summ.get(chat_id)
    def add_message(self, **kw): self.ops.append(("add", kw))

class Container:
    def __init__(self):
        self.short_mem=ShortMemFake()
        self.durable_mem=DurableMemFake()
        class L: 
            def invoke(self, m): return AIMessage(content="ai")
        self.llm=L()
        def tts(x): return b"bytes"
        self.tts=tts
        def img(p): return "img.png"
        self.image_gen=img

class DummyApp:
    def __init__(self, c): self.bot_data={"container": c}

class DummyContext:
    def __init__(self, c): self.application=DummyApp(c)

class DummyUser: 
    id=1; first_name="A"; last_name="B"; username="u"

class DummyChat:
    id=10; type=types.SimpleNamespace(value="private")
    title=None

class DummyUpdate:
    def __init__(self):
        self.effective_user=DummyUser()
        self.effective_chat=DummyChat()

def test_container_from_ctx():
    c = Container()
    ctx = DummyContext(c)
    got = th._container_from_ctx(ctx)
    assert got is c

def test_build_context_includes_summary(monkeypatch):
    c = Container()
    c.durable_mem.summ[10] = "prev summary"
    ctx = th._build_context(c, 10, "hello")
    assert any(isinstance(m, SystemMessage) and "(summary)" in m.content for m in ctx)
    assert isinstance(ctx[-1], HumanMessage)
    assert ctx[-1].content == "hello"

def test_after_reply_triggers_summary(monkeypatch):
    c = Container()
    # force summarize when len(window) >= settings.window_size
    monkeypatch.setattr("app.adapters.telegram_handlers.settings", 
                        types.SimpleNamespace(window_size=1))
    # make summarize_window return fixed text
    monkeypatch.setattr("app.adapters.telegram_handlers.summarize_window",
                        lambda llm, w: "compact summary")
    th._after_reply(c, chat_id=10, user_msg="u", ai_msg="a")
    # set_summary called and short_mem cleared then a (summary) SystemMessage appended
    assert ("set_summary", 10, "compact summary") in c.durable_mem.ops
    assert ("clear", 10) in c.short_mem.ops
    win = c.short_mem.get_window(10)
    assert any(isinstance(m, SystemMessage) and "(summary)" in m.content for m in win)
