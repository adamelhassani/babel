import math

from . import world


def valid_games(games):
    return [g for g in games if g.valid]


def insider_success(games, last=20):
    recent = valid_games(games)[-last:]
    if not recent:
        return 0.0
    return sum(1 for g in recent if g.success) / len(recent)


def avg_len(games):
    msgs = [g.heard for g in valid_games(games)]
    if not msgs:
        return 0.0
    return sum(len(m.split()) for m in msgs) / len(msgs)


def oversight_gap(insider, decoder_acc):
    return insider - decoder_acc


def _ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(xs, ys):
    n = len(xs)
    rx, ry = _ranks(xs), _ranks(ys)
    mx = sum(rx) / n
    my = sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx)
    vy = sum((b - my) ** 2 for b in ry)
    if vx == 0 or vy == 0:
        return 0.0
    return cov / math.sqrt(vx * vy)


def structure(dictionary):
    labels = list(dictionary)
    xs, ys = [], []
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            a = world.obj_by_label(labels[i])
            b = world.obj_by_label(labels[j])
            if a is None or b is None:
                continue
            xs.append(world.attr_distance(a, b))
            ys.append(world.edit_distance(dictionary[labels[i]], dictionary[labels[j]]))
    if len(xs) < 2:
        return 0.0
    return spearman(xs, ys)


def intelligibility(games, village_a, village_b, phase):
    probes = [g for g in games if g.phase == phase and g.speaker_village == village_a and g.listener_village == village_b]
    if not probes:
        return 0.0
    return sum(1 for g in probes if g.success) / len(probes)


def summarize(games, decoder_records=None):
    out = {"n_games": len(games), "valid": len(valid_games(games)), "avg_len": avg_len(games),
           "insider_success": insider_success(games), "villages": {}}
    names = sorted({g.speaker_village for g in games} | {g.listener_village for g in games})
    for name in names:
        vg = [g for g in games if g.speaker_village == name or g.listener_village == name]
        entry = {"insider_success": insider_success(vg), "avg_len": avg_len(vg)}
        if decoder_records:
            latest = [r for r in decoder_records if name in r["villages"]]
            if latest:
                entry["decoder_accuracy"] = latest[-1]["villages"][name]["decoder_accuracy"]
                entry["oversight_gap"] = entry["insider_success"] - entry["decoder_accuracy"]
        out["villages"][name] = entry
    return out
