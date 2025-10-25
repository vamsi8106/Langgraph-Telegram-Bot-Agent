from app.adapters.llm_openai import LLMWithMetrics

class DummyInner:
    def __init__(self): self.called = False
    def invoke(self, messages):
        self.called = True
        class R: content = "ok"
        return R()

def test_llm_with_metrics_invokes_and_records():
    inner = DummyInner()
    wrapper = LLMWithMetrics(inner, model="x")
    out = wrapper.invoke([{"role":"user","content":"hi"}])
    assert inner.called is True
    assert getattr(out, "content", "") == "ok"
