import json
import os
import re

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import config

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


@app.get("/api/runs/{run_id}/rounds")
def run_rounds(run_id: str):
    if not RUN_ID_RE.match(run_id):
        raise HTTPException(400, "invalid run_id")
    path = os.path.join(RUNS_DIR, run_id, "rounds.jsonl")
    if not os.path.isfile(path):
        raise HTTPException(404, f"run {run_id} not found")
    rounds = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rounds.append(json.loads(line))
    return {"run_id": run_id, "rounds": rounds}


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
