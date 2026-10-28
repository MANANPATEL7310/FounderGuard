"""OpenAI-compatible LLM client with caching, validation, and one repair attempt."""
import hashlib
import json
import logging
from typing import Any, Dict, Optional
import httpx

from backend.config import (
    ENABLE_LLM,
    LLM_API_BASE,
    LLM_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_TIMEOUT_SECONDS,
)
from backend.recommendations.prompts import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    build_recommendation_prompt,
    build_repair_prompt,
)
from backend.recommendations.validator import RecommendationValidator
from backend.schemas.recommendation import RecommendationResponse

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self):
        # In-memory prompt cache: key -> RecommendationResponse
        self._cache: Dict[str, RecommendationResponse] = {}

    def _compute_cache_key(self, prompt: str, model: str) -> str:
        raw = f"{PROMPT_VERSION}:{model}:{prompt}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def generate_recommendations(
        self,
        grounding_pack: Dict[str, Any],
    ) -> Optional[RecommendationResponse]:
        """
        Calls the local/remote OpenAI-compatible LLM endpoint with grounding,
        validates the output, executes one repair attempt if needed, and caches the result.
        Returns None if LLM is disabled, unconfigured, or fails both attempts.
        """
        if not ENABLE_LLM or not LLM_MODEL or not LLM_MODEL.strip():
            logger.info("LLM generation skipped: ENABLE_LLM is false or LLM_MODEL is not set.")
            return None

        user_prompt = build_recommendation_prompt(grounding_pack)
        cache_key = self._compute_cache_key(user_prompt, LLM_MODEL)

        if cache_key in self._cache:
            logger.info("Serving LLM recommendations from in-memory cache.")
            return self._cache[cache_key]

        headers = {"Content-Type": "application/json"}
        if LLM_API_KEY and LLM_API_KEY.strip():
            headers["Authorization"] = f"Bearer {LLM_API_KEY.strip()}"

        endpoint = f"{LLM_API_BASE.rstrip('/')}/chat/completions"

        # ── 1. First Attempt ────────────────────────────────────────────────────────
        payload = {
            "model": LLM_MODEL.strip(),
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": LLM_TEMPERATURE,
            "max_tokens": 2500,
        }

        try:
            with httpx.Client(timeout=float(LLM_TIMEOUT_SECONDS)) as client:
                res = client.post(endpoint, json=payload, headers=headers)
                if res.status_code != 200:
                    logger.warning(f"LLM server returned HTTP {res.status_code}: {res.text[:300]}")
                    return None

                res_json = res.json()
                raw_content = res_json["choices"][0]["message"]["content"]

                # Validate
                is_valid, errors, validated_resp = RecommendationValidator.validate(
                    raw_content, grounding_pack
                )

                if is_valid and validated_resp:
                    validated_resp.generation_method = "llm_direct"
                    self._cache[cache_key] = validated_resp
                    return validated_resp

                logger.warning(f"LLM initial output failed validation with {len(errors)} errors: {errors}. Attempting repair...")

                # ── 2. One Repair Attempt ───────────────────────────────────────────
                repair_prompt = build_repair_prompt(user_prompt, raw_content, errors)
                repair_payload = {
                    "model": LLM_MODEL.strip(),
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                        {"role": "assistant", "content": raw_content},
                        {"role": "user", "content": repair_prompt},
                    ],
                    "temperature": 0.1,  # Lower temperature for precision repair
                    "max_tokens": 2500,
                }

                repair_res = client.post(endpoint, json=repair_payload, headers=headers)
                if repair_res.status_code != 200:
                    logger.warning(f"LLM repair attempt failed with HTTP {repair_res.status_code}")
                    return None

                repair_json = repair_res.json()
                repair_content = repair_json["choices"][0]["message"]["content"]

                rep_valid, rep_errors, rep_resp = RecommendationValidator.validate(
                    repair_content, grounding_pack
                )

                if rep_valid and rep_resp:
                    logger.info("LLM output successfully repaired.")
                    rep_resp.generation_method = "llm_repaired"
                    self._cache[cache_key] = rep_resp
                    return rep_resp

                logger.warning(f"LLM repair attempt also failed validation: {rep_errors}. Falling back to template.")
                return None

        except Exception as e:
            logger.warning(f"Error calling LLM at {endpoint}: {str(e)}. Proceeding with playbook fallback.")
            return None


# Singleton instance
llm_client = LLMClient()

