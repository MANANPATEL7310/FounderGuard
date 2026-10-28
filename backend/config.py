"""Backend configuration and constants."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = ROOT_DIR
MODELS_DIR = ROOT_DIR / "models"
MANIFEST_PATH = MODELS_DIR / "manifest.json"

# Load .env file from project root if present
load_dotenv(ROOT_DIR / ".env")

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

# LLM Configuration (never hard-code model name)
LLM_API_BASE = os.environ.get("LLM_API_BASE", "http://localhost:11434/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "")
LLM_TIMEOUT_SECONDS = int(os.environ.get("LLM_TIMEOUT_SECONDS", "45"))
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.2"))
ENABLE_LLM = os.environ.get("ENABLE_LLM", "true").lower() in ("true", "1", "yes")

