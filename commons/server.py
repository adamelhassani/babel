import asyncio
import csv
import json
import os
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import audio as audiomod
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


class SpeakBody(BaseModel):
    text: str
    voice: str = audiomod.DEFAULT_VOICE


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


@app.get("/api/batch")
def batch_results():
    path = os.path.join(RUNS_DIR, "batch", "results.csv")
    if not os.path.isfile(path):
        raise HTTPException(404, "runs/batch/results.csv not found")
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    columns = list(rows[0].keys()) if rows else []
    return {"columns": columns, "rows": rows}


@app.get("/api/runs/{run_id}/inspector")
def run_inspector(run_id: str):
    if not RUN_ID_RE.match(run_id):
        raise HTTPException(400, "invalid run_id")
    path = os.path.join(RUNS_DIR, run_id, "inspector.jsonl")
    if not os.path.isfile(path):
        raise HTTPException(404, f"no inspector.jsonl for {run_id} yet")
    checks = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                checks.append(json.loads(line))
    return {"run_id": run_id, "checks": checks}


@app.post("/transcribe")
async def transcribe(request: Request):
    body = await request.body()
    if not body:
        raise HTTPException(400, "empty audio body")
    try:
        text = await audiomod.transcribe(body)
    except Exception as exc:
        raise HTTPException(502, f"transcribe failed: {exc}")
    return {"text": text}


@app.post("/speak")
async def speak(body: SpeakBody):
    try:
        data = await asyncio.to_thread(audiomod.speak, body.text, body.voice)
    except Exception as exc:
        raise HTTPException(502, f"speak failed: {exc}")
    return Response(content=data, media_type="audio/wav")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
