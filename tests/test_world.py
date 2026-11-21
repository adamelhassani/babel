import asyncio
import random

from babel import world


class Fake:
    def __init__(self, name, village, shared, message="ka", cheat=True):
        self.name = name
        self.village = village
        self.shared = shared
        self.message = message
        self.cheat = cheat
        self.learned = []
        self.listen_calls = 0

    async def speak(self, target, options, round_no=1, max_len=None):
        self.shared["target"] = target.label()
        return self.message

    async def listen(self, message, options, round_no=1):
        self.listen_calls += 1
        if self.cheat:
            return options.index(world.obj_by_label(self.shared["target"]))
        return 0

    def learn(self, feedback):
        self.learned.append(feedback)


def test_message_regex():
    assert world.is_valid_message("ka")
    assert world.is_valid_message("ka mo ti")
    assert not world.is_valid_message("ka mo ti zu")
    assert not world.is_valid_message("hello")
    assert not world.is_valid_message("")
    assert not world.is_valid_message("ka  mo")
    assert world.is_valid_message("ka mo ti zu", max_len=4)


def test_noise():
    rng = random.Random(0)
    assert world.apply_noise("ka mo", 0.0, rng) == "ka mo"
    noisy = world.apply_noise("ka mo ti", 1.0, rng)
    assert len(noisy.split(" ")) == 3
    assert all(s in world.config.SYLLABLES for s in noisy.split(" "))


def test_distances():
    a = world.obj_by_label("small red circle")
    b = world.obj_by_label("small blue circle")
    c = world.obj_by_label("large blue triangle")
    assert world.attr_distance(a, a) == 0
    assert world.attr_distance(a, b) == 1
    assert world.attr_distance(a, c) == 3
    assert world.edit_distance("ka mo", "ka mo") == 0
    assert world.edit_distance("ka", "ka mo") == 1
    assert world.edit_distance("ka ti", "mo ti") == 1


def test_play_game_success():
    shared = {}
    speaker = Fake("s", "v0", shared)
    listener = Fake("l", "v0", shared)
    game = asyncio.run(world.play_game(1, 1, "isolation", speaker, listener, max_len=3, noise=0.0, n_distractors=3))
    assert game.valid and game.success
    assert game.choice == game.options.index(game.target)
    assert listener.listen_calls == 1
    assert speaker.learned and listener.learned


def test_play_game_invalid_never_reaches_listener():
    shared = {}
    speaker = Fake("s", "v0", shared, message="hello")
    listener = Fake("l", "v0", shared)
    game = asyncio.run(world.play_game(2, 1, "isolation", speaker, listener, max_len=3))
    assert not game.valid
    assert game.choice is None and not game.success
    assert listener.listen_calls == 0
