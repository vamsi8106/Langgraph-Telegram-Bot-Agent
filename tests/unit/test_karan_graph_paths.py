# import pytest
# from langchain_core.messages import HumanMessage, AIMessage
# from app.workflows.karan_graph import build_graph
# from app.di import Container
# from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, RemoveMessage

# class DummyLLM:
#     def invoke(self, messages):
#         # echo minimal AI response
#         return AIMessage(content="ok from dummy llm")

# def dummy_tts(text: str) -> bytes:
#     return b"voice-bytes"

# def dummy_image_gen(prompt: str, size: str = "1024x1024") -> str:
#     return "fake.png"

# @pytest.fixture
# def container():
#     # swap in dummies so no network calls
#     return Container(llm=DummyLLM(), vector=None, tts=dummy_tts, image_gen=dummy_image_gen)

# def test_text_flow(container, monkeypatch):
#     # router → text (force text by making random low and no voice/image keywords)
#     monkeypatch.setattr("app.workflows.karan_graph.random.random", lambda: 0.0)
#     g = build_graph(container)
#     out = g.invoke({"messages": [HumanMessage(content="hello")]}
#                    , {"configurable": {"thread_id": "t1"}})
#     assert out.get("response_type") in {"text", None}
#     # last message should be AIMessage appended by text node
#     assert isinstance(out["messages"][-1], AIMessage)

# def test_audio_flow(container):
#     g = build_graph(container)
#     out = g.invoke({"messages": [HumanMessage(content="please send a voice note")]}
#                    , {"configurable": {"thread_id": "t2"}})
#     assert out["response_type"] == "audio"
#     assert out["audio_buffer"] == b"voice-bytes"

# def test_image_flow(container):
#     g = build_graph(container)
#     out = g.invoke({"messages": [HumanMessage(content="send a selfie pic")]}
#                    , {"configurable": {"thread_id": "t3"}})
#     assert out["response_type"] == "image"
#     assert out["image_path"] == "fake.png"

# def _summarize_node(container):
#     def _fn(state: KaranState):
#         msgs = state.get("messages", [])
#         window = msgs[-20:]  # summarize recent context
#         prompt = HumanMessage(content="Summarize the conversation above in 3 lines to keep context compact.")
#         resp = container.llm.invoke(window + [prompt])
#         summary = getattr(resp, "content", "")

#         # REMOVE all existing messages, then add a single compact SystemMessage
#         deletes = [RemoveMessage(id=m.id) for m in msgs]
#         return {"messages": deletes + [SystemMessage(content=f"(summary) {summary}")]}
#     return _fn

# def test_summarize_path(container, monkeypatch):
#     # ensure router goes to text (not audio random)
#     monkeypatch.setattr("app.workflows.karan_graph.random.random", lambda: 0.0)
#     g = build_graph(container)
#     many = [HumanMessage(content=f"m{i}") for i in range(31)]
#     out = g.invoke({"messages": many}, {"configurable": {"thread_id": "t4"}})
#     # summarizer replaces message history with a single SystemMessage containing summary
#     assert len(out["messages"]) == 1
#     assert "(summary)" in out["messages"][0].content

# tests/unit/test_karan_graph_paths.py
import pytest
from langchain_core.messages import HumanMessage, AIMessage
from app.workflows.karan_graph import build_graph

def _close(g):
    conn = getattr(g, "_conn", None)
    if conn:
        conn.close()

def test_text_flow(container, monkeypatch):
    # Force router to choose "text" by making random low and no voice/image keywords
    monkeypatch.setattr("app.workflows.karan_graph.random.random", lambda: 0.0)
    g = build_graph(container, attach_conn_for_tests=True)
    try:
        out = g.invoke({"messages": [HumanMessage(content="hello")]},
                       {"configurable": {"thread_id": "t1"}})
        assert out.get("response_type") in {"text", None}
        assert isinstance(out["messages"][-1], AIMessage)
        assert out["messages"][-1].content
    finally:
        _close(g)

def test_audio_flow(container):
    g = build_graph(container, attach_conn_for_tests=True)
    try:
        out = g.invoke({"messages": [HumanMessage(content="please send a voice note")]},
                       {"configurable": {"thread_id": "t2"}})
        assert out["response_type"] == "audio"
        assert out["audio_buffer"] == b"voice-bytes"
    finally:
        _close(g)

def test_image_flow(container):
    g = build_graph(container, attach_conn_for_tests=True)
    try:
        out = g.invoke({"messages": [HumanMessage(content="send a selfie pic")]},
                       {"configurable": {"thread_id": "t3"}})
        assert out["response_type"] == "image"
        assert out["image_path"] == "fake.png"
    finally:
        _close(g)

