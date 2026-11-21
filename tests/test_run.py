import asyncio
import json
import os
import random

from babel import config, run as runmod, world


class Fake:
    def __init__(self, name, village, seed=None):
        self.name = name
        self.village = village
        self.learned = []

    async def speak(self, target, options, round_no=1, max_len=None):
        return "ka"

    async def listen(self, message, options, round_no=1):
        return 0

    def learn(self, feedback):
        self.learned.append(feedback)

    async def name_objects(self):
        return {o.label(): "ka" for o in world.OBJECTS}


def factory(name, village, seed):
    return Fake(name, village, seed)


def test_gamelog_writes_jsonl(tmp_path):
    log = runmod.GameLog(str(tmp_path))
    g = world.Game(1, 1, "isolation", "a", "v0", "b", "v0", "small red circle", ["small red circle"], "ka", "ka", True, 0, True)
    log.append(g)
    log.close()
    with open(tmp_path / "games.jsonl") as fh:
        data = json.loads(fh.readline())
    assert data["speaker"] == "a"
    assert world.Game.from_dict(data).success is True


def test_isolation_pairs():
    agents = [Fake(str(i), "v0") for i in range(4)]
    pairs = runmod.isolation_pairs(agents, random.Random(0))
    assert len(pairs) == 2
    flat = [a for pair in pairs for a in pair]
    assert sorted(a.name for a in flat) == ["0", "1", "2", "3"]


def test_run_experiment_tiny(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ISOLATION_ROUNDS", 2)
    monkeypatch.setattr(config, "CONTACT_ROUNDS", 2)
    monkeypatch.setattr(config, "N_VILLAGES", 2)
    monkeypatch.setattr(config, "VILLAGERS_PER_VILLAGE", 2)
    run_dir = runmod.new_run_dir(str(tmp_path))
    asyncio.run(runmod.run_experiment(run_dir, {"MAX_LEN": 3, "NOISE": 0.0, "N_DISTRACTORS": 3},
                                      factory=factory, checkpoint_every=999))
    with open(os.path.join(run_dir, "games.jsonl")) as fh:
        games = [json.loads(line) for line in fh]
    phases = {g["phase"] for g in games}
    assert "isolation" in phases and "contact" in phases
    assert any(p.startswith("probe@") for p in phases)
