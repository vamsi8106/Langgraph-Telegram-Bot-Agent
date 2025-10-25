# src/app/adapters/tts_elevenlabs.py
from __future__ import annotations

from elevenlabs.client import ElevenLabs
from ..config.settings import settings


def build_tts():
    """
    Build a text-to-speech (TTS) synthesizer using the ElevenLabs API.

    Returns
    -------
    Callable[[str], bytes]
        A `_synth(text)` function that converts input text to speech audio
        and returns it as raw byte data (for Telegram or file saving).
    """
    client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

    def _synth(text: str) -> bytes:
        """
        Convert the given text into spoken audio using ElevenLabs.

        Parameters
        ----------
        text : str
            The text content to synthesize.

        Returns
        -------
        bytes
            The full audio byte stream (concatenated from ElevenLabs chunks).
        """
        stream = client.text_to_speech.convert(
            text=text,
            voice_id=settings.elevenlabs_voice_id,
            model_id=settings.elevenlabs_model_id,
        )
        return b"".join(stream)

    return _synth
