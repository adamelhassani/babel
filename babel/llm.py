import asyncio
import base64
import json

from mistralai.client import Mistral

from . import config

_client = None
_semaphore = asyncio.Semaphore(config.CONCURRENCY)


def client():
    global _client
    if _client is None:
        if not config.MISTRAL_API_KEY:
            raise RuntimeError("MISTRAL_API_KEY is not set in the environment")
        _client = Mistral(api_key=config.MISTRAL_API_KEY, timeout_ms=config.TIMEOUT_S * 1000)
    return _client


async def call_model_json(model, messages, temperature=0.7):
    async with _semaphore:
        last_exc = None
        for _ in range(config.RETRIES + 1):
            try:
                resp = await client().chat.complete_async(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"},
                )
                return json.loads(resp.choices[0].message.content)
            except Exception as exc:
                last_exc = exc
        raise last_exc


def tts_bytes(text):
    resp = client().audio.speech.complete(model=config.TTS_MODEL, input=text)
    data = getattr(resp, "audio_data", None) or getattr(resp, "audio", None) or getattr(resp, "data", None)
    if isinstance(data, bytes):
        return data
    return base64.b64decode(data)
