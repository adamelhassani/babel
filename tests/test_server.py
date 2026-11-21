import json
import os

from fastapi.testclient import TestClient

from babel import config, server


def _seed_run(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RUNS_DIR", str(tmp_path))
    run_dir = os.path.join(str(tmp_path), "run1")
    os.makedirs(run_dir)
    game = {"game_id": 1, "round_no": 1, "phase": "isolation", "speaker": "a", "speaker_village": "v0",
            "listener": "b", "listener_village": "v0", "target": "small red circle",
            "options": ["small red circle"], "message": "ka", "heard": "ka", "valid": True, "choice": 0, "success": True}
    with open(os.path.join(run_dir, "games.jsonl"), "w") as fh:
        fh.write(json.dumps(game) + "\n")
    return "run1"


def test_list_and_read_run(tmp_path, monkeypatch):
    run_id = _seed_run(tmp_path, monkeypatch)
    client = TestClient(server.app)
    assert client.get("/api/runs").json() == {"runs": [run_id]}
    state = client.get(f"/api/run/{run_id}").json()
    assert state["games"][0]["success"] is True
    assert state["metrics"]["n_games"] == 1
    assert len(client.get(f"/api/run/{run_id}/games").json()["games"]) == 1


def test_unknown_run_404(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RUNS_DIR", str(tmp_path))
    client = TestClient(server.app)
    assert client.get("/api/run/nope").status_code == 404
