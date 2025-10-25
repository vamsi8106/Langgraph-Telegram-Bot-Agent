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

