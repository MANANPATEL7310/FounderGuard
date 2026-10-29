"""Location lists, state mappings, and country codes."""
from typing import Dict, List, Optional, Tuple

SUPPORTED_COUNTRIES: List[Dict[str, str]] = [
    {"code": "USA", "name": "United States"},
    {"code": "GBR", "name": "United Kingdom"},
    {"code": "CAN", "name": "Canada"},
    {"code": "DEU", "name": "Germany"},
    {"code": "FRA", "name": "France"},
    {"code": "IND", "name": "India"},
    {"code": "AUS", "name": "Australia"},
    {"code": "SGP", "name": "Singapore"},
    {"code": "ISR", "name": "Israel"},
    {"code": "OTHER", "name": "Other Country"},
]

US_STATES: List[Dict[str, str]] = [
    {"code": "CA", "name": "California"},
    {"code": "NY", "name": "New York"},
    {"code": "MA", "name": "Massachusetts"},
    {"code": "TX", "name": "Texas"},
    {"code": "WA", "name": "Washington"},
    {"code": "IL", "name": "Illinois"},
    {"code": "CO", "name": "Colorado"},
    {"code": "FL", "name": "Florida"},
    {"code": "NC", "name": "North Carolina"},
    {"code": "PA", "name": "Pennsylvania"},
    {"code": "GA", "name": "Georgia"},
    {"code": "OTHER", "name": "Other US State"},
]

MODEL_B_MAJOR_STATES = {"CA", "NY", "MA", "TX"}

def normalize_location(country: str, state: Optional[str] = None) -> Tuple[str, str, str, bool]:
    """
    Normalizes country and state.
    Returns (country_code, raw_state, model_b_state_group, is_us).
    """
    country_code = (country or "USA").strip().upper()
    is_us = country_code in ("USA", "US", "UNITED STATES")
    
    st = (state or "").strip().upper() if state else ""
    if not is_us:
        model_b_state = "OTHER"
        country_code = country_code if country_code else "OTHER"
    else:
        country_code = "USA"
        model_b_state = st if st in MODEL_B_MAJOR_STATES else "OTHER"
        if not st:
            st = "OTHER"
            
    return country_code, st, model_b_state, is_us

