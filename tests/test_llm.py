import asyncio
from types import SimpleNamespace

from babel import llm


def _resp(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


class FakeChat:
    def __init__(self, failures_before_success):
        self.failures = failures_before_success
        self.calls = 0

    async def complete_async(self, **kwargs):
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("boom")
        return _resp('{"message": "ka"}')


class FakeClient:
    def __init__(self, chat):
        self.chat = chat


def test_retries_then_success(monkeypatch):
    chat = FakeChat(2)
    monkeypatch.setattr(llm, "_client", FakeClient(chat))
    out = asyncio.run(llm.call_model_json("m", [{"role": "user", "content": "hi"}]))
    assert out == {"message": "ka"}
    assert chat.calls == 3


def test_raises_after_retries(monkeypatch):
    chat = FakeChat(99)
    monkeypatch.setattr(llm, "_client", FakeClient(chat))
    try:
        asyncio.run(llm.call_model_json("m", []))
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "boom" in str(exc)


def test_missing_key_raises(monkeypatch):
    monkeypatch.setattr(llm, "_client", None)
    monkeypatch.setattr(llm.config, "MISTRAL_API_KEY", "")
    try:
        llm.client()
        assert False, "expected RuntimeError"
    except RuntimeError as exc:
        assert "MISTRAL_API_KEY" in str(exc)
