import base64, os
from app.adapters.image_openai import build_image_gen

def test_image_gen_monkeypatched(tmp_path, monkeypatch):
    # Use a valid tiny PNG (1x1 transparent) as raw bytes
    tiny_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc`\x00\x00\x00\x02\x00\x01"
        b"\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    b64 = base64.b64encode(tiny_png).decode()

    class Result:
        class DataItem:
            b64_json = b64
        data = [DataItem()]

    class DummyClient:
        class images:
            @staticmethod
            def generate(**kwargs):
                return Result()

    monkeypatch.setenv("OPENAI_API_KEY", "test")  # ensure client init doesn't choke
    monkeypatch.setattr("app.adapters.image_openai.OpenAI", lambda **_: DummyClient)

    # run
    gen = build_image_gen()
    path = gen("test", size="512x512")

    # assert
    assert path.endswith(".png")
    assert os.path.exists(path)
    with open(path, "rb") as f:
        assert f.read() == tiny_png
