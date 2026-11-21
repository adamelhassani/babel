import asyncio
import json
import os
import random

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config, llm, metrics, run as runmod, world

app = FastAPI(title="Babel")
RUNS = {}

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")


class StartBody(BaseModel):
    preset: str = "low"
    backend: str = "B"
    auto_open: bool = False


class ControlBody(BaseModel):
    action: str
    params: dict = {}


class TradeOfferBody(BaseModel):
    run_id: str
    village: str


class TradeCommitBody(BaseModel):
    run_id: str
    offer_id: int
    message: str
    choice: int


def _run_path(run_id):
    return os.path.join(config.RUNS_DIR, run_id)


def load_games(run_id):
    path = os.path.join(_run_path(run_id), "games.jsonl")
    if not os.path.exists(path):
        raise HTTPException(404, f"run {run_id} not found")
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(world.Game.from_dict(json.loads(line)))
    return out


def load_records(run_id):
    path = os.path.join(_run_path(run_id), "metrics.jsonl")
    out = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
    return out


@app.post("/api/run/start")
async def start_run(body: StartBody):
    if body.preset not in config.PRESETS:
        raise HTTPException(400, f"unknown preset {body.preset}")
    dials = dict(config.PRESETS[body.preset])
    run_dir = runmod.new_run_dir()
    run_id = os.path.basename(run_dir)
    event = asyncio.Event()
    state = {"dials": dials, "offers": {}}
    RUNS[run_id] = {"event": event, "state": state}
    task = asyncio.create_task(runmod.run_experiment(run_dir, dials, backend=body.backend,
                                                     auto_open=body.auto_open, open_event=event, run_state=state))
    RUNS[run_id]["task"] = task
    return {"run_id": run_id}


@app.get("/api/runs")
def list_runs():
    if not os.path.isdir(config.RUNS_DIR):
        return {"runs": []}
    return {"runs": sorted(d for d in os.listdir(config.RUNS_DIR) if os.path.isdir(os.path.join(config.RUNS_DIR, d)))}


@app.get("/api/run/{run_id}")
def run_state(run_id: str):
    games = load_games(run_id)
    records = load_records(run_id)
    return {"run_id": run_id, "games": [g.to_dict() for g in games], "records": records,
            "metrics": metrics.summarize(games, records)}


@app.get("/api/run/{run_id}/games")
def run_games(run_id: str):
    return {"games": [g.to_dict() for g in load_games(run_id)]}


@app.post("/api/run/{run_id}/control")
async def control(run_id: str, body: ControlBody):
    if run_id not in RUNS:
        raise HTTPException(404, "run not active in this server process")
    if body.action == "open_trade":
        RUNS[run_id]["event"].set()
    elif body.action == "set_dials":
        for key in ("MAX_LEN", "NOISE", "N_DISTRACTORS"):
            if key in body.params:
                RUNS[run_id]["state"]["dials"][key] = body.params[key]
    else:
        raise HTTPException(400, f"unknown action {body.action}")
    return {"ok": True, "dials": RUNS[run_id]["state"]["dials"]}


@app.post("/api/trade/offer")
def trade_offer(body: TradeOfferBody):
    if body.run_id not in RUNS:
        raise HTTPException(404, "run not active in this server process")
    state = RUNS[body.run_id]["state"]
    if body.village not in state.get("villages", {}):
        raise HTTPException(400, f"unknown village {body.village}")
    rng = random.Random()
    target = rng.choice(world.OBJECTS)
    pool = [o for o in world.OBJECTS if o != target]
    options = rng.sample(pool, min(state["dials"]["N_DISTRACTORS"], len(pool))) + [target]
    rng.shuffle(options)
    offer_id = len(state["offers"]) + 1
    state["offers"][offer_id] = {"target": target.label(), "options": [o.label() for o in options], "village": body.village}
    return {"offer_id": offer_id, "options": [o.label() for o in options]}


@app.post("/api/trade/commit")
async def trade_commit(body: TradeCommitBody):
    if body.run_id not in RUNS:
        raise HTTPException(404, "run not active in this server process")
    state = RUNS[body.run_id]["state"]
    offer = state["offers"].pop(body.offer_id, None)
    if offer is None:
        raise HTTPException(404, "unknown offer_id")
    rng = random.Random()
    listener = rng.choice(state["villages"][offer["village"]])
    options_objs = [world.obj_by_label(label) for label in offer["options"]]
    valid = world.is_valid_message(body.message, state["dials"]["MAX_LEN"])
    choice = None
    success = False
    heard = body.message
    if valid:
        heard = world.apply_noise(body.message, state["dials"]["NOISE"], rng)
        choice = await listener.listen(heard, options_objs)
        success = 0 <= choice < len(options_objs) and options_objs[choice].label() == offer["target"]
    log = state["log"]
    game = world.Game(game_id=len(log.games) + 1, round_no=0, phase="human",
                      speaker="human", speaker_village="human",
                      listener=listener.name, listener_village=listener.village,
                      target=offer["target"], options=offer["options"],
                      message=body.message, heard=heard, valid=valid, choice=choice, success=success)
    log.append(game)
    listener.learn({"message": heard, "options": offer["options"], "choice": choice,
                    "target": offer["target"], "success": success, "valid": valid})
    return {"valid": valid, "heard": heard, "choice": choice, "success": success, "target": offer["target"]}


@app.get("/api/audio")
def audio(text: str):
    return Response(content=llm.tts_bytes(text), media_type="audio/wav")


if os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
