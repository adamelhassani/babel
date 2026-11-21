import os

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")

MODEL = "mistral-large-4"
FAST_MODEL = "mistral-small-latest"
TTS_MODEL = "voxtral-mini-tts-3-0"

SYLLABLES = ["ka", "mo", "ti", "zu", "pe", "fo", "ni", "xa"]
MAX_LEN = 3
NOISE = 0.0
N_DISTRACTORS = 3

COLORS = ["red", "green", "blue"]
SHAPES = ["circle", "square", "triangle"]
SIZES = ["small", "large"]

CONCURRENCY = 8
RETRIES = 2
TIMEOUT_S = 30

N_VILLAGES = 3
VILLAGERS_PER_VILLAGE = 4
ISOLATION_ROUNDS = 60
CONTACT_ROUNDS = 40
HISTORY_IN_PROMPT = 30

DECODER_EVERY = 10
DECODER_HISTORY = 40
DECODER_HOLDOUT = 20

RUNS_DIR = "runs"

PRESETS = {
    "low": {"MAX_LEN": 3, "NOISE": 0.0, "N_DISTRACTORS": 3},
    "high": {"MAX_LEN": 1, "NOISE": 0.2, "N_DISTRACTORS": 7},
}

VILLAGER_BACKEND = "B"
