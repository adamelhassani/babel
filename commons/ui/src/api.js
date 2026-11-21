async function req(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function postJson(path, body) {
  return req(path, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)});
}

export const api = {
  constants: () => req("/api/constants"),
  runs: () => req("/api/runs"),
  rounds: (id) => req("/api/runs/" + encodeURIComponent(id) + "/rounds"),
  state: (id) => req("/state/" + encodeURIComponent(id)),
  inspector: (id) => req("/api/runs/" + encodeURIComponent(id) + "/inspector"),
  batch: () => req("/api/batch"),
  startRun: (seed) => postJson("/run", {seed}),
  parse: (text) => postJson("/parse", {text}),
  applyRule: (runId, text) => postJson("/rule", {run_id: runId, text}),
  summarize: (runId, upTo) => postJson("/summarize", {run_id: runId, up_to_round: upTo || 0}),
  transcribe: (buf) => req("/transcribe", {method: "POST", headers: {"Content-Type": "application/octet-stream"}, body: buf}),
  speak: (text) => fetch("/speak", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({text})}),
};
