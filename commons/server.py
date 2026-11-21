import json
import os
import re

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config
from . import rules as rulesmod
from . import run as runmod

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS_DIR = os.path.join(REPO_ROOT, config.RUNS_DIR)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

app = FastAPI(title="Commons")


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/constants")
def constants():
    return {
        "K": config.K,
        "F_DEAD": config.F_DEAD,
        "SUSTAINABLE_CATCH": config.SUSTAINABLE_CATCH,
        "PER_FISHER_SUSTAINABLE": config.SUSTAINABLE_CATCH / config.N,
        "C_MAX": config.C_MAX,
        "N": config.N,
    }


@app.get("/api/runs")
def list_runs():
    runs = []
    if os.path.isdir(RUNS_DIR):
        for name in sorted(os.listdir(RUNS_DIR)):
            if os.path.isfile(os.path.join(RUNS_DIR, name, "rounds.jsonl")):
                runs.append(name)
    return {"runs": runs}


class StartBody(BaseModel):
    seed: int = 0


class RuleBody(BaseModel):
    run_id: str
    text: str


def _rounds_path(run_id):
    if not RUN_ID_RE.match(run_id):
        raise HTTPException(400, "invalid run_id")
    path = os.path.join(RUNS_DIR, run_id, "rounds.jsonl")
    if not os.path.isfile(path):
        raise HTTPException(404, f"run {run_id} not found")
    return path


def _read_rounds(run_id):
    rounds = []
    with open(_rounds_path(run_id), encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rounds.append(json.loads(line))
    return rounds


def _run_active(run_id):
    entry = runmod._RUNS.get(run_id)
    return bool(entry and not entry["task"].done())


@app.get("/api/runs/{run_id}/rounds")
def run_rounds(run_id: str):
    return {"run_id": run_id, "rounds": _read_rounds(run_id)}


@app.post("/run")
async def start(body: StartBody):
    run_id = runmod.start_run(body.seed)
    return {"run_id": run_id}


@app.post("/rule")
async def apply_rule_text(body: RuleBody):
    if body.run_id not in runmod._RUNS:
        raise HTTPException(404, f"run {body.run_id} is not active in this server process")
    try:
        rule = await rulesmod.parse_rule(body.text)
    except Exception as exc:
        raise HTTPException(502, f"rule parser failed: {exc}")
    runmod.apply_rule(body.run_id, rule)
    return {"run_id": body.run_id, "rule": rule}


@app.get("/state/{run_id}")
def state(run_id: str):
    rounds = _read_rounds(run_id)
    return {
        "run_id": run_id,
        "rounds": rounds,
        "round": rounds[-1]["round"] if rounds else 0,
        "active": _run_active(run_id),
    }


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
