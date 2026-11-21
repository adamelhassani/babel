import os

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")

FISHER_MODEL = "mistral-medium-latest"
LARGE_MODEL = "mistral-large-4"
TTS_MODEL = "voxtral-mini-tts-3-0"
TRANSCRIBE_MODEL = "voxtral-mini-transcribe-3-0"

K = 1000
R = 0.25
F0 = 600
N = 10
C_MAX = 20
LIVING = 5
F_DEAD = 50
T = 40

SUSTAINABLE_CATCH = R * K / 4

CONCURRENCY = 10
FISHER_TIMEOUT_S = 20
FISHER_RETRIES = 1
FISHER_MAX_TOKENS = 80
REASONING_EFFORT = "none"

PHASE0_SEEDS = [0, 1, 2]
PHASE0_ROUNDS = 30

RUNS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runs")
