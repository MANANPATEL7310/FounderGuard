"""Backend API client with timeout and retry for safe GET calls."""
from __future__ import annotations
import time
import requests
import streamlit as st
from frontend.config import BACKEND_URL, REQUEST_TIMEOUT, OPTIONS_CACHE_TTL


def _url(path: str) -> str:
    return f"{BACKEND_URL}{path}"


def _get(path: str, retries: int = 2) -> dict:
    for attempt in range(retries + 1):
        try:
            r = requests.get(_url(path), timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError:
            if attempt == retries:
                raise
            time.sleep(0.5)
    return {}


def _post(path: str, payload: dict) -> requests.Response:
    return requests.post(_url(path), json=payload, timeout=REQUEST_TIMEOUT)


# ── Cached options fetch ──────────────────────────────────────────────────────
@st.cache_data(ttl=OPTIONS_CACHE_TTL)
def fetch_options() -> dict:
    try:
        return _get("/v1/meta/options")
    except Exception:
        return {}


# ── Validate (no store) ───────────────────────────────────────────────────────
def validate_submission(payload: dict) -> tuple[bool, dict]:
    """Returns (ok, body). body contains 'detail' on error."""
    try:
        r = _post("/v1/evaluations/validate", payload)
        if r.status_code == 200:
            return True, r.json()
        return False, r.json()
    except requests.exceptions.ConnectionError:
        return False, {"detail": "Cannot reach the backend. Is the server running?"}
    except Exception as e:
        return False, {"detail": str(e)}


# ── Submit evaluation ─────────────────────────────────────────────────────────
def submit_evaluation(payload: dict) -> tuple[bool, dict]:
    try:
        r = _post("/v1/evaluations", payload)
        if r.status_code == 202:
            return True, r.json()
        return False, r.json()
    except requests.exceptions.ConnectionError:
        return False, {"detail": "Cannot reach the backend."}
    except Exception as e:
        return False, {"detail": str(e)}


# ── Status poll ───────────────────────────────────────────────────────────────
def get_status(eval_id: str) -> dict | None:
    try:
        return _get(f"/v1/evaluations/{eval_id}")
    except Exception:
        return None


# ── Report ────────────────────────────────────────────────────────────────────
def get_report(eval_id: str) -> dict | None:
    try:
        return _get(f"/v1/evaluations/{eval_id}/report")
    except Exception:
        return None


# ── Delete ────────────────────────────────────────────────────────────────────
def delete_evaluation(eval_id: str) -> bool:
    try:
        r = requests.delete(_url(f"/v1/evaluations/{eval_id}"), timeout=REQUEST_TIMEOUT)
        return r.status_code == 200
    except Exception:
        return False


# ── Backend health ────────────────────────────────────────────────────────────
def check_backend_health() -> bool:
    try:
        r = requests.get(_url("/health"), timeout=5)
        return r.status_code == 200
    except Exception:
        return False

