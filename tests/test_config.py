from babel import config, world


def test_eighteen_objects():
    assert len(world.OBJECTS) == 18


def test_model_defaults_to_large():
    assert config.MODEL == "mistral-large-4"
    assert config.FAST_MODEL


def test_presets():
    assert set(config.PRESETS) == {"low", "high"}
    assert config.PRESETS["high"]["MAX_LEN"] == 1
    assert config.PRESETS["high"]["NOISE"] == 0.2
    assert config.PRESETS["high"]["N_DISTRACTORS"] == 7
