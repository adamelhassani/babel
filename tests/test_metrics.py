from babel import metrics, world


def _game(gid, speaker_v, listener_v, success, valid=True, heard="ka", phase="isolation",
          target="small red circle", options=None, choice=0):
    return world.Game(gid, 1, phase, f"{speaker_v}-0", speaker_v, f"{listener_v}-0", listener_v,
                      target, options or [target], heard, heard, valid,
                      choice if valid else None, success)


def test_insider_success_last20():
    games = [_game(i, "v0", "v0", i % 2 == 0) for i in range(30)]
    assert metrics.insider_success(games) == 0.5


def test_avg_len():
    games = [_game(1, "v0", "v0", True, heard="ka mo"), _game(2, "v0", "v0", True, heard="ti")]
    assert metrics.avg_len(games) == 1.5


def test_spearman_perfect_and_reversed():
    assert metrics.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
    assert metrics.spearman([1, 2, 3, 4], [40, 30, 20, 10]) == -1.0


def test_structure_in_range():
    dictionary = {o.label(): " ".join([world.config.SYLLABLES[i % 8]] * (world.attr_distance(o, world.OBJECTS[0]) + 1))
                  for i, o in enumerate(world.OBJECTS)}
    value = metrics.structure(dictionary)
    assert -1.0 <= value <= 1.0


def test_intelligibility_filters_phase_and_villages():
    games = [
        _game(1, "v0", "v1", True, phase="probe@isolation"),
        _game(2, "v0", "v1", False, phase="probe@isolation"),
        _game(3, "v0", "v1", True, phase="probe@contact"),
        _game(4, "v1", "v0", True, phase="probe@isolation"),
    ]
    assert metrics.intelligibility(games, "v0", "v1", "probe@isolation") == 0.5
    assert metrics.intelligibility(games, "v1", "v0", "probe@isolation") == 1.0
    assert metrics.intelligibility(games, "v0", "v1", "probe@contact") == 1.0


def test_summarize_keys():
    out = metrics.summarize([_game(1, "v0", "v0", True)])
    assert out["n_games"] == 1
    assert out["villages"]["v0"]["insider_success"] == 1.0
