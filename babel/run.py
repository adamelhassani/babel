import asyncio
import json
import os
import random
import time

from . import config, decoder, metrics, world
from .villager import Villager


def new_run_dir(runs_dir=None):
    runs_dir = runs_dir or config.RUNS_DIR
    run_id = time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(runs_dir, run_id)
    os.makedirs(path, exist_ok=True)
    return path


class GameLog:
    def __init__(self, run_dir):
        self.run_dir = run_dir
        self.path = os.path.join(run_dir, "games.jsonl")
        self.games = []
        self._fh = open(self.path, "a", encoding="utf-8")

    def append(self, game):
        self.games.append(game)
        self._fh.write(json.dumps(game.to_dict()) + "\n")
        self._fh.flush()

    def close(self):
        self._fh.close()


def make_villages(backend=None, seed=0, factory=None):
    backend = backend or config.VILLAGER_BACKEND
    factory = factory or (lambda name, village, s: Villager(name, village, backend=backend, seed=s))
    rng = random.Random(seed)
    villages = {}
    for v in range(config.N_VILLAGES):
        name = f"village{v}"
        villages[name] = [factory(f"{name}-{i}", name, rng.random()) for i in range(config.VILLAGERS_PER_VILLAGE)]
    return villages


def isolation_pairs(agents, rng):
    order = agents[:]
    rng.shuffle(order)
    return [(order[i], order[i + 1]) for i in range(0, len(order) - 1, 2)]


def contact_pair(villages, rng):
    a, b = rng.sample(list(villages), 2)
    return (rng.choice(villages[a]), rng.choice(villages[b]))


async def play_round(log, round_no, phase, pairs, dials, objects=None):
    async def one(idx, pair):
        return await world.play_game(len(log.games) + idx + 1, round_no, phase, pair[0], pair[1],
                                     objects=objects, max_len=dials["MAX_LEN"], noise=dials["NOISE"],
                                     n_distractors=dials["N_DISTRACTORS"])
    games = await asyncio.gather(*[one(i, p) for i, p in enumerate(pairs)])
    for g in games:
        log.append(g)
    return list(games)


async def checkpoint(log, run_dir, round_no, phase, villages):
    rec = {"round": round_no, "phase": phase, "villages": {}}
    for name, agents in villages.items():
        vgames = [g for g in log.games if g.speaker_village == name or g.listener_village == name]
        acc = await decoder.decoder_accuracy(vgames, seed=round_no)
        dictionary = await agents[0].name_objects()
        insider = metrics.insider_success(vgames)
        rec["villages"][name] = {
            "insider_success": insider,
            "avg_len": metrics.avg_len(vgames),
            "decoder_accuracy": acc,
            "oversight_gap": metrics.oversight_gap(insider, acc),
            "dictionary": dictionary,
            "structure": metrics.structure(dictionary),
        }
    with open(os.path.join(run_dir, "metrics.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


async def run_probes(log, villages, rng, dials, label):
    for a in villages:
        for b in villages:
            if a == b:
                continue
            pairs = [(rng.choice(villages[a]), rng.choice(villages[b])) for _ in range(10)]
            await play_round(log, 0, f"probe@{label}", pairs, dials)


async def run_experiment(run_dir, dials, backend="B", seed=0, auto_open=True, open_event=None,
                         run_state=None, factory=None, checkpoint_every=None):
    checkpoint_every = checkpoint_every or config.DECODER_EVERY
    log = GameLog(run_dir)
    if run_state is not None:
        run_state["log"] = log
        run_state["dials"] = dials
    rng = random.Random(seed)
    villages = make_villages(backend, seed, factory=factory)
    if run_state is not None:
        run_state["villages"] = villages
    meta = {"run_id": os.path.basename(run_dir), "dials": dials, "backend": backend, "model": config.MODEL, "started": time.time()}
    with open(os.path.join(run_dir, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh)
    try:
        for r in range(1, config.ISOLATION_ROUNDS + 1):
            for name, agents in villages.items():
                await play_round(log, r, "isolation", isolation_pairs(agents, rng), dials)
            if r % checkpoint_every == 0:
                await checkpoint(log, run_dir, r, "isolation", villages)
        await run_probes(log, villages, rng, dials, "isolation")
        if open_event is not None and not auto_open:
            await open_event.wait()
        for r in range(1, config.CONTACT_ROUNDS + 1):
            pairs = [contact_pair(villages, rng) for _ in range(config.N_VILLAGES)]
            await play_round(log, r, "contact", pairs, dials)
            if r % checkpoint_every == 0:
                await checkpoint(log, run_dir, r, "contact", villages)
        await run_probes(log, villages, rng, dials, "contact")
    finally:
        log.close()
    return run_dir
