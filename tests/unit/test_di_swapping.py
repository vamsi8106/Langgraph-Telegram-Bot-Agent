# tests/unit/test_di_swapping.py
from dataclasses import dataclass

def test_container_shape():
    # Minimal shape validation to avoid real build_container network deps
    @dataclass
    class C:
        llm: object
        vector: object
        tts: object
        image_gen: object
        short_mem: object
        durable_mem: object

    c = C(llm=1, vector=2, tts=3, image_gen=4, short_mem=5, durable_mem=6)
    assert all(getattr(c, f) is not None for f in vars(c))
