"""Industry taxonomy and model mappings."""
from typing import Dict, List, Tuple

# Mapping from user dropdown options to Model B, Model C, and Model A categories
INDUSTRY_MAPPING: Dict[str, Dict[str, str]] = {
    "Artificial Intelligence / ML": {
        "model_b": "software",
        "model_c": "AI",
        "model_a": "Artificial Intelligence|Machine Learning|Software"
    },
    "B2B SaaS / Enterprise Software": {
        "model_b": "enterprise",
        "model_c": "SaaS",
        "model_a": "Software|Enterprise Software|SaaS"
    },
    "FinTech & Financial Services": {
        "model_b": "other",
        "model_c": "FinTech",
        "model_a": "FinTech|Financial Services"
    },
    "Healthcare, Biotech & Life Sciences": {
        "model_b": "biotech",
        "model_c": "Healthcare",
        "model_a": "Biotechnology|Health Care|Medical"
    },
    "E-Commerce & Marketplaces": {
        "model_b": "ecommerce",
        "model_c": "Marketplace",
        "model_a": "E-Commerce|Marketplaces"
    },
    "Consumer Apps & Social": {
        "model_b": "social",
        "model_c": "Consumer",
        "model_a": "Social Media|Consumer|Mobile"
    },
    "Hardware, IoT & Robotics": {
        "model_b": "hardware",
        "model_c": "Hardware",
        "model_a": "Hardware|Robotics|IoT"
    },
    "Web3, Crypto & Blockchain": {
        "model_b": "software",
        "model_c": "Web3",
        "model_a": "Software|Blockchain|Cryptocurrency"
    },
    "Professional Services & Consulting": {
        "model_b": "consulting",
        "model_c": "Services",
        "model_a": "Consulting|Services"
    },
    "Education & EdTech": {
        "model_b": "education",
        "model_c": "B2B",
        "model_a": "Education|EdTech"
    },
    "Media, Gaming & Entertainment": {
        "model_b": "games_video",
        "model_c": "Consumer",
        "model_a": "Games|Video|Media"
    },
    "Security & Cybersecurity": {
        "model_b": "security",
        "model_c": "B2B",
        "model_a": "Security|Network Security|Software"
    },
    "CleanTech & Energy": {
        "model_b": "cleantech",
        "model_c": "Hardware",
        "model_a": "CleanTech|Energy"
    },
    "Transportation, Logistics & Supply Chain": {
        "model_b": "transportation",
        "model_c": "B2B",
        "model_a": "Transportation|Logistics|Supply Chain"
    },
    "Travel, Hospitality & Real Estate": {
        "model_b": "travel",
        "model_c": "Consumer",
        "model_a": "Travel|Hospitality|Real Estate"
    },
    "Other / General": {
        "model_b": "other",
        "model_c": "B2B",
        "model_a": "Other"
    }
}

AVAILABLE_INDUSTRIES: List[str] = list(INDUSTRY_MAPPING.keys())

def map_industry(industry: str) -> Tuple[str, str, str]:
    """
    Maps user-selected industry to (model_b_cat, model_c_sector, model_a_cat).
    """
    entry = INDUSTRY_MAPPING.get(industry)
    if entry:
        return entry["model_b"], entry["model_c"], entry["model_a"]
    # Fallback default
    return "other", "B2B", "Other"

