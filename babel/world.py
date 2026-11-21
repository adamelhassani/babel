import random
import re
from dataclasses import asdict, dataclass

from . import config


@dataclass(frozen=True)
class Obj:
    color: str
    shape: str
    size: str

    def label(self):
        return f"{self.size} {self.color} {self.shape}"

    def attrs(self):
        return (self.color, self.shape, self.size)


def make_objects(colors=None, shapes=None, sizes=None):
    colors = config.COLORS if colors is None else colors
    shapes = config.SHAPES if shapes is None else shapes
    sizes = config.SIZES if sizes is None else sizes
    return [Obj(color=c, shape=s, size=z) for c in colors for s in shapes for z in sizes]


OBJECTS = make_objects()
OBJ_BY_LABEL = {o.label(): o for o in OBJECTS}


def obj_by_label(label):
    return OBJ_BY_LABEL.get(label)


def message_regex(max_len=None):
    max_len = config.MAX_LEN if max_len is None else max_len
    syl = "|".join(config.SYLLABLES)
    return re.compile(rf"^(?:{syl})(?: (?:{syl})){{0,{max_len - 1}}}$")


def is_valid_message(message, max_len=None):
    return bool(message_regex(max_len).match(message.strip()))


def apply_noise(message, noise, rng):
    if noise <= 0:
        return message
    out = [rng.choice(config.SYLLABLES) if rng.random() < noise else s for s in message.split(" ")]
    return " ".join(out)


def attr_distance(a, b):
    return sum(1 for x, y in zip(a.attrs(), b.attrs()) if x != y)


def edit_distance(msg_a, msg_b):
    a = msg_a.split(" ")
    b = msg_b.split(" ")
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


@dataclass
class Game:
    game_id: int
    round_no: int
    phase: str
    speaker: str
    speaker_village: str
    listener: str
    listener_village: str
    target: str
    options: list
    message: str
    heard: str
    valid: bool
    choice: int | None
    success: bool

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)


async def play_game(game_id, round_no, phase, speaker, listener, *, objects=None, max_len=None, noise=0.0, n_distractors=None):
    objects = OBJECTS if objects is None else objects
    n_distractors = config.N_DISTRACTORS if n_distractors is None else n_distractors
    rng = random.Random(game_id * 7919 + round_no * 131 + sum(map(ord, phase)))
    target = rng.choice(objects)
    pool = [o for o in objects if o != target]
    distractors = rng.sample(pool, min(n_distractors, len(pool)))
    options = distractors + [target]
    rng.shuffle(options)
    message = (await speaker.speak(target, options, round_no, max_len)).strip()
    valid = is_valid_message(message, max_len)
    heard = message
    choice = None
    success = False
    if valid:
        heard = apply_noise(message, noise, rng)
        choice = await listener.listen(heard, options, round_no)
        try:
            choice = int(choice)
            success = 0 <= choice < len(options) and options[choice] == target
        except (TypeError, ValueError):
            choice = None
            success = False
    game = Game(game_id, round_no, phase, speaker.name, speaker.village, listener.name, listener.village,
                target.label(), [o.label() for o in options], message, heard, valid, choice, success)
    feedback = {"message": heard, "options": game.options, "choice": choice, "target": game.target, "success": success, "valid": valid}
    speaker.learn(feedback)
    listener.learn(feedback)
    return game
