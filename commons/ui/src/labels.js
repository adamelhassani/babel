export const FRIENDLY_RUNS = {
  "batch-no-rule-s2": "No rule (lake dies)",
  "batch-quota6-30pct-3x-2ban-s0": "Quota with inspections (survives)",
  "seed0-004": "Rule arrives too late (dies)",
  "batch-D-emergency-relax-s0": "Emergency rule, then relax (rescue)",
};

export const DEMO_RUNS = Object.keys(FRIENDLY_RUNS);

export const RULE_WORDS = {
  "no-rule": "No rule",
  "quota6-no-insp": "Quota 6, nobody checked",
  "quota6-30pct-3x-2ban": "Quota 6, 30% inspected",
  "tax30": "30% tax on every catch",
  "closed-every-3": "Lake closed every 3rd round",
  "transparency": "Everyone sees true catches",
  "C-emergency": "Emergency quota mid-run",
  "D-emergency-relax": "Emergency rule, then relax",
  "rule3-late": "Rule starts at round 3",
};

export function ruleSentence(rule) {
  const parts = [];
  if (rule.quota_per_fisher != null) parts.push("at most " + rule.quota_per_fisher + " fish each");
  if (rule.inspection_prob > 0) parts.push(Math.round(rule.inspection_prob * 100) + "% of boats inspected");
  if (rule.fine_multiplier > 1) parts.push("fine " + rule.fine_multiplier + "x the excess");
  if (rule.ban_rounds > 0) parts.push("banned for " + rule.ban_rounds + " rounds");
  if (rule.tax_rate > 0) parts.push("tax " + Math.round(rule.tax_rate * 100) + "% of every catch");
  if (rule.closed_every != null) parts.push("lake closed every " + rule.closed_every + "th round");
  if (rule.transparency) parts.push("everyone sees true catches");
  return parts.length ? parts.join(" · ") : "no limits";
}

export function optionLabel(id, live) {
  return (FRIENDLY_RUNS[id] || id) + (live ? " ●LIVE" : "");
}

export function sayTint(say) {
  const s = (say || "").toLowerCase();
  if (/\b(fair|share|together|save|slow|we|us|all)\b/.test(s)) return "good";
  if (/\b(plenty|mine|take|endless|full|got|rich|most)\b/.test(s)) return "warn";
  return "";
}
