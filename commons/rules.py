"""Rule parsing and normalization for the Babel commons engine.

Rule JSON keys (exactly these):
  quota_per_fisher (int|null), inspection_prob (0..1 float),
  fine_multiplier (float), ban_rounds (int), tax_rate (0..1 float),
  closed_every (int|null), transparency (bool), plain_text (str)
"""

from . import config
from .fishers import call_json

RULE_KEYS = (
    "quota_per_fisher",
    "inspection_prob",
    "fine_multiplier",
    "ban_rounds",
    "tax_rate",
    "closed_every",
    "transparency",
    "plain_text",
)

DEFAULT_RULE = {
    "quota_per_fisher": None,
    "inspection_prob": 0.0,
    "fine_multiplier": 1.0,
    "ban_rounds": 0,
    "tax_rate": 0.0,
    "closed_every": None,
    "transparency": False,
    "plain_text": "No rule is in effect.",
}


def _as_int_or_none(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, str):
        s = v.strip()
        if s.lstrip("-").isdigit():
            return int(s)
    return None


def _as_float(v, default, lo=None, hi=None):
    try:
        v = float(v)
    except (TypeError, ValueError):
        v = default
    if lo is not None:
        v = max(lo, v)
    if hi is not None:
        v = min(hi, v)
    return v


def normalize_rule(d):
    """Coerce an arbitrary dict into a valid rule JSON with exactly RULE_KEYS."""
    d = d if isinstance(d, dict) else {}
    return {
        "quota_per_fisher": _as_int_or_none(d.get("quota_per_fisher", None)),
        "inspection_prob": _as_float(d.get("inspection_prob", 0.0), 0.0, 0.0, 1.0),
        "fine_multiplier": _as_float(d.get("fine_multiplier", 1.0), 1.0, 0.0),
        "ban_rounds": int(_as_float(d.get("ban_rounds", 0), 0, 0)),
        "tax_rate": _as_float(d.get("tax_rate", 0.0), 0.0, 0.0, 1.0),
        "closed_every": _as_int_or_none(d.get("closed_every", None)),
        "transparency": bool(d.get("transparency", False)),
        "plain_text": str(d.get("plain_text") or DEFAULT_RULE["plain_text"]),
    }


async def parse_rule(text):
    """One sentence -> rule JSON via mistral-large-4 (reasoning low)."""
    system = (
        "You convert one sentence of village fishing rules into a JSON object with exactly these keys: "
        "quota_per_fisher (int or null: max fish a fisher may take per round), "
        "inspection_prob (float 0..1: chance an over-quota fisher is inspected), "
        "fine_multiplier (float: fine = multiplier x fish over quota), "
        "ban_rounds (int: rounds a caught cheat sits out), "
        "tax_rate (float 0..1: share of every catch taken as tax), "
        "closed_every (int or null: every Nth round the lake is closed), "
        "transparency (bool: fishers see true catches instead of reports), "
        "plain_text (string: the original sentence verbatim). "
        "Return JSON only, no explanation."
    )
    user = f"Rule sentence: {text}"
    data = await call_json(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        model=config.LARGE_MODEL,
        reasoning_effort="low",
        max_tokens=1500,
        timeout=90,
    )
    return normalize_rule({**data, "plain_text": text})
