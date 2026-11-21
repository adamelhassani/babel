import base64

from . import config
from .fishers import client

DEFAULT_VOICE = "gb_jane_neutral"


def speak(text, voice=DEFAULT_VOICE):
    resp = client().audio.speech.complete(
        model=config.TTS_MODEL,
        input=text,
        voice_id=voice,
        response_format="wav",
    )
    return base64.b64decode(resp.audio_data)


async def transcribe(audio_bytes):
    resp = await client().audio.transcriptions.complete_async(
        model=config.TRANSCRIBE_MODEL,
        file={"file_name": "audio.wav", "content": audio_bytes},
    )
    return resp.text
