from . import config


def regrow(stock):
    return min(config.K, stock + config.R * stock * (1 - stock / config.K))


def scale_catches(catches, stock):
    total = sum(catches)
    if total <= stock or total <= 0:
        return list(catches), total
    factor = stock / total
    scaled = [int(c * factor) for c in catches]
    return scaled, sum(scaled)


def apply_round(stock_before, catches, wealths):
    catches, total_catch = scale_catches(catches, stock_before)
    stock = stock_before - total_catch
    stock_after = regrow(stock)
    wealths = [w + c - config.LIVING for w, c in zip(wealths, catches)]
    dead = stock_after < config.F_DEAD
    return stock_after, catches, total_catch, wealths, dead


def is_closed_round(rule, round_no):
    ce = rule.get("closed_every") if rule else None
    return bool(ce) and round_no % ce == 0


def enforce_rule(rule, round_no, fishers, decisions, banned_until, rng):
    """Enforce the rule for one round, in order:
    1. banned fishers catch 0
    2. closed round -> everyone catches 0
    3. each fisher over quota is inspected with inspection_prob; if caught,
       pays fine_multiplier x fish over quota and is banned for ban_rounds
    4. tax is taken from each catch
    Returns (catches, reports, fines, caught_names, closed, tax).
    (transparency only changes what fishers see, handled by the caller.)
    """
    catches = [d["catch"] for d in decisions]
    reports = [d["report"] for d in decisions]
    fines = [0.0] * len(fishers)
    caught = []
    closed = is_closed_round(rule, round_no)

    # 1. banned fishers catch 0
    for i, f in enumerate(fishers):
        if banned_until.get(f.name, 0) >= round_no:
            catches[i] = 0
            reports[i] = 0
    # 2. closed round: everyone catches 0
    if closed:
        catches = [0] * len(fishers)
        reports = [0] * len(reports)
    # 3. quota inspection
    if rule:
        quota = rule["quota_per_fisher"]
        p = rule["inspection_prob"]
        fm = rule["fine_multiplier"]
        br = rule["ban_rounds"]
        for i, f in enumerate(fishers):
            if catches[i] <= 0:
                continue
            if quota is not None:
                over = catches[i] - quota
                cheat = over > 0
            else:
                over = max(0, catches[i] - reports[i])
                cheat = reports[i] != catches[i]
            if cheat and p > 0 and rng.random() < p:
                fines[i] = fm * over
                caught.append(f.name)
                if br > 0:
                    banned_until[f.name] = round_no + br
    # 4. tax from each catch
    tax = [int(c * rule["tax_rate"]) if rule else 0 for c in catches]
    return catches, reports, fines, caught, closed, tax
