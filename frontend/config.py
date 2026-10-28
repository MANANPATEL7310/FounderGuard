"""Frontend configuration — read from environment, never hard-code."""
import os

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "20"))
POLL_INTERVAL_S = float(os.environ.get("POLL_INTERVAL_S", "1.5"))
MAX_POLL_ATTEMPTS = int(os.environ.get("MAX_POLL_ATTEMPTS", "60"))
OPTIONS_CACHE_TTL = int(os.environ.get("OPTIONS_CACHE_TTL", "300"))

