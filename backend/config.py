"""Backend configuration and constants."""
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT_DIR / "models"
MANIFEST_PATH = MODELS_DIR / "manifest.json"

# Limits & defaults
MODEL_TIMEOUT_SECONDS = 15
MAX_IDEA_CHARS = 4000
MIN_IDEA_CHARS = 20
MAX_PROBLEM_CHARS = 1000
MAX_TARGET_CUSTOMER_CHARS = 500
MAX_FIELD_LENGTH = 1000

# Training data boundaries
MODEL_A_MAX_TRAINING_YEAR = 2015
MODEL_B_MIN_FUNDING_USD = 1.0

