# tests/unit/test_telegram_handlers.py
import pytest
from langchain_core.messages import HumanMessage
from app.adapters.telegram_handlers import _send_response


class DummyMsg:
    def __init__(self):
        self.sent = {"text": [], "voice": [], "photo": []}
    async def reply_text(self, t): self.sent["text"].append(t)
    async def reply_voice(self, voice=None): self.sent["voice"].append(voice)
    async def reply_photo(self, photo=None): self.sent["photo"].append(photo)


class DummyUpdate:
    def __init__(self): self.message = DummyMsg()


class DummyCtx: pass


@pytest.mark.asyncio
async def test_send_response_text():
    update = DummyUpdate()
    resp = {"messages": [HumanMessage(content="hi")], "response_type": "text"}
    await _send_response(update, DummyCtx(), resp)
    assert update.message.sent["text"] == ["hi"]


@pytest.mark.asyncio
async def test_send_response_audio():
    update = DummyUpdate()
    resp = {"messages": [HumanMessage(content="x")], "response_type": "audio", "audio_buffer": b"bytes"}
    await _send_response(update, DummyCtx(), resp)
    assert update.message.sent["voice"] == [b"bytes"]


@pytest.mark.asyncio
async def test_send_response_image(tmp_path):
    # create a temp image file
    p = tmp_path / "x.png"
    p.write_bytes(b"png-bytes")
    update = DummyUpdate()
    resp = {"messages": [HumanMessage(content="x")], "response_type": "image", "image_path": str(p)}
    await _send_response(update, DummyCtx(), resp)
    assert len(update.message.sent["photo"]) == 1
