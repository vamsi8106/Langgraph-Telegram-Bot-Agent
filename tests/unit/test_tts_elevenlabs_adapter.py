# from app.adapters.tts_elevenlabs import build_tts

# def test_tts_synth_monkeypatched(monkeypatch):
#     class DummyTextToSpeech:
#         @staticmethod
#         def convert(**kwargs):
#             yield b"abc"
#             yield b"123"

#     class DummyClient:
#         text_to_speech = DummyTextToSpeech()

#     monkeypatch.setattr("app.adapters.tts_elevenlabs.ElevenLabs", lambda **_: DummyClient)
#     synth = build_tts()
#     data = synth("hello")
#     assert isinstance(data, bytes)
#     assert data == b"abc123"


# tests/unit/test_tts_elevenlabs_adapter.py
from app.adapters.tts_elevenlabs import build_tts

def test_tts_synth_monkeypatched(monkeypatch):
    class DummyTextToSpeech:
        @staticmethod
        def convert(**kwargs):
            yield b"abc"
            yield b"123"

    class DummyClient:
        text_to_speech = DummyTextToSpeech()

    monkeypatch.setattr("app.adapters.tts_elevenlabs.ElevenLabs", lambda **_: DummyClient)
    synth = build_tts()
    data = synth("hello")
    assert isinstance(data, bytes)
    assert data == b"abc123"
