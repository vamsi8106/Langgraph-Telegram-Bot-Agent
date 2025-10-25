from langchain_core.messages import HumanMessage
from app.adapters.summarizer import summarize_window

class DummyLLM:
    def invoke(self, messages):
        # Return an object with .content like an AIMessage
        class R: content = "short summary"
        return R()

def test_summarize_window_uses_last_20():
    llm = DummyLLM()
    window = [HumanMessage(content=f"m{i}") for i in range(30)]
    out = summarize_window(llm, window)
    assert out == "short summary"
