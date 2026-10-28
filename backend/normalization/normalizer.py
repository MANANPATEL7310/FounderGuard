"""Input normalization pipeline and payload builder."""
import re
from typing import Any, Dict, List, Tuple
from backend.normalization.currency import convert_to_usd
from backend.normalization.industry import map_industry
from backend.normalization.locations import normalize_location
from backend.schemas.submission import SubmissionInput

def clean_str(text: str) -> str:
    """Strip HTML, markdown artifacts, and collapse whitespace."""
    if not text:
        return ""
    t = str(text)
    # Strip HTML tags
    t = re.sub(r"<[^>]+>", " ", t)
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t

class Normalizer:
    @staticmethod
    def normalize(sub: SubmissionInput) -> Tuple[Dict[str, Any], List[str]]:
        """
        Executes the 10-step normalization pipeline.
        Returns (normalized_dict, warnings).
        """
        warnings = []
        
        # 1. Clean free-text fields
        idea_clean = clean_str(sub.idea_description)
        problem_clean = clean_str(sub.problem_statement)
        customer_clean = clean_str(sub.target_customer)
        val_clean = clean_str(sub.validation_evidence)
        comp_clean = clean_str(sub.competitors)
        traction_clean = clean_str(sub.traction)
        
        # 2. Currency conversion
        funding_usd, ex_rate, ex_date = convert_to_usd(sub.funding_raised, sub.currency)
        
        # 3. Location normalization
        country_code, state_clean, model_b_state_group, is_us = normalize_location(sub.country, sub.state)
        if not is_us and sub.country != "USA":
            warnings.append(f"Startup location '{country_code}' is outside the US. Model B training data was US-only.")

        # 4. Industry mapping
        model_b_cat, model_c_sector, model_a_cat = map_industry(sub.industry)

        # 5. Model B Investor and Round flags
        inv_types = [t.lower() for t in (sub.investor_types or [])]
        has_vc = 1 if any("venture" in t or "vc" in t for t in inv_types) else 0
        has_angel = 1 if any("angel" in t for t in inv_types) else 0
        
        r_reached = [r.lower() for r in (sub.rounds_reached or [])]
        has_roundA = 1 if any("round a" in r for r in r_reached) else 0
        has_roundB = 1 if any("round b" in r for r in r_reached) else 0
        has_roundC = 1 if any("round c" in r for r in r_reached) else 0
        has_roundD = 1 if any("round d" in r for r in r_reached) else 0
        
        # 6. Model C extra dictionary
        model_c_extra = {}
        if problem_clean:
            model_c_extra["problem"] = problem_clean
        if customer_clean:
            model_c_extra["target_customer"] = customer_clean
        if sub.business_model:
            model_c_extra["business_model"] = ", ".join(sub.business_model)
        if val_clean:
            model_c_extra["validation_evidence"] = val_clean
        if comp_clean:
            model_c_extra["competitors"] = comp_clean
        if traction_clean:
            model_c_extra["traction"] = traction_clean

        # 7. Model D composed text recipe
        # Recipe: join in order: idea, problem, business model, team, validation. No negative filler.
        parts = [idea_clean]
        if problem_clean:
            parts.append(problem_clean)
        if sub.business_model:
            parts.append(f"Business model: {', '.join(sub.business_model)}.")
        
        team_parts = [f"Team size: {sub.team_size}"]
        if sub.team_skills:
            team_parts.append(f"skills in {', '.join(sub.team_skills)}")
        if sub.founder_experience:
            team_parts.append(f"founder experience: {sub.founder_experience}")
        parts.append(f"Team: {', '.join(team_parts)}.")
        
        if val_clean:
            parts.append(f"Validation: {val_clean}.")
            
        model_d_text = " ".join(parts)

        # 8. Provenance tracking
        provided = ["idea_description", "industry", "country"]
        missing = []
        
        for k, v in [
            ("problem_statement", problem_clean),
            ("target_customer", customer_clean),
            ("state", state_clean),
            ("validation_evidence", val_clean),
            ("competitors", comp_clean),
            ("traction", traction_clean),
            ("homepage_url", sub.homepage_url),
            ("city", sub.city),
            ("region", sub.region),
            ("founded_at", sub.founded_at),
            ("first_funding_at", sub.first_funding_at),
            ("last_funding_at", sub.last_funding_at),
        ]:
            if v:
                provided.append(k)
            else:
                missing.append(k)

        # 9. Pack complete normalized object
        normalized = {
            "idea_description": idea_clean,
            "problem_statement": problem_clean,
            "target_customer": customer_clean,
            "industry": sub.industry,
            "country": country_code,
            "state": state_clean,
            "target_market": sub.target_market,
            "business_model": sub.business_model,
            "stage": sub.stage,
            "funding_total_usd": funding_usd,
            "funding_rounds": sub.funding_rounds,
            "original_funding": sub.funding_raised,
            "original_currency": sub.currency,
            "exchange_rate_used": ex_rate,
            "exchange_rate_date": ex_date,
            "budget_available": sub.budget_available,
            
            # Model payloads
            "model_a_payload": {
                "homepage_url": sub.homepage_url,
                "category_list": model_a_cat,
                "funding_total_usd": funding_usd,
                "country_code": country_code,
                "state_code": state_clean,
                "region": sub.region,
                "city": sub.city,
                "funding_rounds": sub.funding_rounds,
                "founded_at": sub.founded_at,
                "first_funding_at": sub.first_funding_at,
                "last_funding_at": sub.last_funding_at,
            },
            "model_b_payload": {
                "category_code": model_b_cat,
                "state_code": state_clean,
                "state_group": model_b_state_group,
                "funding_total_usd": funding_usd,
                "funding_rounds": sub.funding_rounds,
                "has_VC": has_vc,
                "has_angel": has_angel,
                "has_roundA": has_roundA,
                "has_roundB": has_roundB,
                "has_roundC": has_roundC,
                "has_roundD": has_roundD,
            },
            "model_c_payload": {
                "idea_text": idea_clean,
                "declared_sector": model_c_sector,
                "extra": model_c_extra,
            },
            "model_d_payload": {
                "text": model_d_text,
                "top_k_cases": 3,
            },
            "provenance": {
                "provided_fields": provided,
                "missing_fields": missing,
            }
        }
        
        return normalized, warnings
