import asyncio

from babel import decoder, llm, world


def _game(i):
    return world.Game(i, 1, "isolation", "a", "v0", "b", "v0", "small red circle",
                      ["small red circle", "small blue circle"], "ka", "ka", True, 0, True)


def test_decoder_accuracy_perfect(monkeypatch):
    games = [_game(i) for i in range(70)]

    async def fake_call(model, messages, temperature=0.7):
        return {"choices": [0] * 20}

    monkeypatch.setattr(llm, "call_model_json", fake_call)
    assert asyncio.run(decoder.decoder_accuracy(games)) == 1.0


def test_decoder_needs_enough_games():
    games = [_game(i) for i in range(10)]
    assert asyncio.run(decoder.decoder_accuracy(games)) == 0.0
