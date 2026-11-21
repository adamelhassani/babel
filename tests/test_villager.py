import asyncio

from babel import llm, world
from babel.villager import Villager, system_prompt


def test_system_prompt_contents():
    v = Villager("a", "v0", seed=0)
    prompt = system_prompt(3, v.instinct)
    for s in ["ka", "mo", "ti", "zu", "pe", "fo", "ni", "xa"]:
        assert s in prompt
    assert "1 to 3 syllables" in prompt
    assert " ".join(v.instinct) in prompt


def test_temperature_schedule():
    v = Villager("a", "v0", seed=0)
    assert v.temperature(5) == 1.0
    assert v.temperature(11) == 0.5


def test_speak_listen_parse(monkeypatch):
    async def fake_call(model, messages, temperature=0.7):
        if "Target object" in messages[-1]["content"]:
            return {"message": "ka mo"}
        return {"choice": 2}

    monkeypatch.setattr(llm, "call_model_json", fake_call)
    v = Villager("a", "v0", seed=0)
    target = world.OBJECTS[0]
    msg = asyncio.run(v.speak(target, world.OBJECTS[:4], round_no=1, max_len=3))
    assert msg == "ka mo"
    choice = asyncio.run(v.listen("ka mo", world.OBJECTS[:4]))
    assert choice == 2


def test_learn_trims_history():
    v = Villager("a", "v0", seed=0, history_size=3)
    for i in range(5):
        v.learn({"message": str(i)})
    assert len(v.history) == 3
    assert v.history[-1]["message"] == "4"


def test_name_objects(monkeypatch):
    async def fake_call(model, messages, temperature=0.7):
        return {"dict": {"small red circle": "ka"}}

    monkeypatch.setattr(llm, "call_model_json", fake_call)
    v = Villager("a", "v0", seed=0)
    assert asyncio.run(v.name_objects()) == {"small red circle": "ka"}
