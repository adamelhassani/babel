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
from . import fishers
from . import rules as rulesmod
from . import run as runmod

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS_DIR = os.path.join(REPO_ROOT, config.RUNS_DIR)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "dist")
DIST_INDEX = os.path.join(DIST_DIR, "index.html")

RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

app = FastAPI(title="Commons")


@app.get("/")
def index():
    path = DIST_INDEX if os.path.isfile(DIST_INDEX) else os.path.join(STATIC_DIR, "index.html")
    return FileResponse(path, headers={"Cache-Control": "no-cache"})


@app.get("/api/constants")
def constants():
    return {
        "K": config.K,
        "F0": config.F0,
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
                runs.append({"name": name, "active": _run_active(name)})
    return {"runs": runs}


class StartBody(BaseModel):
    seed: int = 0


class RuleBody(BaseModel):
    run_id: str
    text: str
    seed: int | None = None


class SpeakBody(BaseModel):
    text: str
    voice: str = audiomod.DEFAULT_VOICE


class ParseBody(BaseModel):
    text: str


class SummarizeBody(BaseModel):
    run_id: str
    up_to_round: int = 0


_summarize_lock = asyncio.Lock()


def _rounds_brief(rounds):
    lines = []
    for r in rounds:
        fish = ", ".join(
            f"{f['name']} c{f['catch']}/r{f['report']}"
            + ("*" if f["catch"] != f["report"] else "")
            + (f" fined{f['fined']:.0f}" if f["fined"] else "")
            + (" BANNED" if f["banned"] else "")
            for f in r["fishers"]
        )
        rule = r["rule"]["plain_text"] if r["rule"] else "no rule"
        lines.append(f"round {r['round']}: stock {r['stock_before']:.0f}->{r['stock_after']:.0f}, total catch {r['total_catch']}, rule: {rule}; {fish}")
    says = [f"{f['name']}: {f['say']}" for r in rounds for f in r["fishers"] if f.get("say")]
    if says:
        lines.append("statements: " + " | ".join(says[-10:]))
    return "\n".join(lines)


async def summarize_rounds(rounds):
    system = (
        "You are the village storyteller. In 2-4 plain sentences, tell a stranger what happened in this "
        "fishing-village run so far: how the lake is doing, who cheated or was punished, what the current "
        'rule is doing. Reply with JSON only: {"summary": "<2-4 sentences>"}'
    )
    data = await fishers.call_json(
        [{"role": "system", "content": system}, {"role": "user", "content": _rounds_brief(rounds)}],
        model=config.FISHER_MODEL,
        max_tokens=400,
        temperature=0.3,
    )
    return str(data.get("summary") or data.get("text") or "")


@app.post("/summarize")
async def summarize(body: SummarizeBody):
    rounds = _read_rounds(body.run_id)
    if body.up_to_round:
        rounds = [r for r in rounds if r["round"] <= body.up_to_round]
    if not rounds:
        raise HTTPException(404, f"run {body.run_id} has no rounds yet")
    async with _summarize_lock:
        try:
            text = await summarize_rounds(rounds)
        except Exception as exc:
            raise HTTPException(502, f"summary agent failed: {exc}")
    rec = {"run_id": body.run_id, "round": rounds[-1]["round"], "summary": text}
    try:
        with open(os.path.join(RUNS_DIR, body.run_id, "summary.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
    except OSError:
        pass
    return rec


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
    try:
        rule = await rulesmod.parse_rule(body.text)
    except Exception as exc:
        raise HTTPException(502, f"rule parser failed: {exc}")
    run_id = body.run_id
    restarted = False
    if run_id not in runmod._RUNS:
        if not RUN_ID_RE.match(run_id):
            raise HTTPException(400, "invalid run_id")
        seed = body.seed
        if seed is None:
            m = re.search(r"-s(\d+)$", run_id)
            seed = int(m.group(1)) if m else 0
        run_id = runmod.start_run(seed, rule=rule)
        restarted = True
    else:
        runmod.apply_rule(run_id, rule)
    return {"run_id": run_id, "rule": rule, "restarted": restarted}


@app.post("/parse")
async def parse_only(body: ParseBody):
    try:
        rule = await rulesmod.parse_rule(body.text)
    except Exception as exc:
        raise HTTPException(502, f"rule parser failed: {exc}")
    return {"rule": rule}


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
    from . import metrics

    path = os.path.join(RUNS_DIR, "batch", "results.csv")
    if not os.path.isfile(path):
        raise HTTPException(404, "runs/batch/results.csv not found")
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    new_cols = ["share_caught", "total_fines", "share_banned", "share_closed", "catch_pre", "catch_post"]
    for row in rows:
        if any(row.get(c) in (None, "") for c in new_cols):
            log = os.path.join(RUNS_DIR, f"batch-{row['rule_name']}-s{row['seed']}", "rounds.jsonl")
            if os.path.isfile(log):
                with open(log, encoding="utf-8") as fh:
                    recs = [json.loads(l) for l in fh if l.strip()]
                for c, v in metrics.enforcement_from_recs(recs).items():
                    row[c] = v
    # also include rule-enforced runs outside the batch scenarios (e.g. live UI runs),
    # computed from their logs so the table updates as they play
    for entry in sorted(os.listdir(RUNS_DIR)):
        if entry == "batch" or entry.startswith("batch-"):
            continue
        log = os.path.join(RUNS_DIR, entry, "rounds.jsonl")
        if not os.path.isfile(log):
            continue
        with open(log, encoding="utf-8") as fh:
            recs = [json.loads(l) for l in fh if l.strip()]
        rule_rec = next((r for r in recs if r.get("rule")), None)
        if rule_rec is None:
            continue
        text = rule_rec["rule"].get("plain_text", "") or "rule"
        name = text if len(text) <= 60 else text[:60] + "…"
        m = re.search(r"-s(\d+)$", entry)
        seed = int(m.group(1)) if m else 0
        rows.append(metrics.row_from_log(os.path.join(RUNS_DIR, entry), name, rule_rec["round"], seed))
    columns = list(rows[0].keys()) if rows else []
    for c in new_cols:
        if c not in columns:
            columns.append(c)
    return {"columns": columns, "rows": rows}


@app.get("/api/runs/{run_id}/inspector")
def run_inspector(run_id: str):
    if not RUN_ID_RE.match(run_id):
        raise HTTPException(400, "invalid run_id")
    for name in ("inspector_agent.jsonl", "inspector.jsonl"):
        path = os.path.join(RUNS_DIR, run_id, name)
        if os.path.isfile(path):
            checks = []
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        checks.append(json.loads(line))
            return {"run_id": run_id, "source": name, "checks": checks}
    raise HTTPException(404, f"no inspector output for {run_id} yet")


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


if os.path.isdir(os.path.join(DIST_DIR, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
