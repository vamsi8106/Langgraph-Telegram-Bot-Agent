# from app.di import build_container
# from app.workflows.karan_graph import build_graph
# from langchain_core.messages import HumanMessage


# def test_graph_invoke_smoke(graph):
#     out = graph.invoke({"messages": [HumanMessage(content="hello karan")]},
#                        {"configurable": {"thread_id": "test"}})
#     assert isinstance(out, dict)

# tests/integration/test_graph_smoke.py
from langchain_core.messages import HumanMessage


def test_graph_invoke_smoke(graph):
    out = graph.invoke({"messages": [HumanMessage(content="hello karan")]},
                       {"configurable": {"thread_id": "test"}})
    assert isinstance(out, dict)
    assert "messages" in out
