"""Shared UI helpers used across all pages."""
from __future__ import annotations


# ── Status/warning banner helpers ─────────────────────────────────────────────

def not_applicable_card(model_name: str, reason: str) -> str:
    return f"""
<div style="border-left:4px solid #9E9E9E;background:#f5f5f5;padding:12px 16px;border-radius:4px;margin:8px 0">
  <strong>⊘ {model_name}: Not Applicable</strong><br>
  <span style="color:#555">{reason}</span>
</div>"""


def error_card(model_name: str, reason: str) -> str:
    return f"""
<div style="border-left:4px solid #F44336;background:#fff3f3;padding:12px 16px;border-radius:4px;margin:8px 0">
  <strong>✕ {model_name}: Unavailable</strong><br>
  <span style="color:#555">{reason}</span>
</div>"""


def ood_banner(model_name: str) -> str:
    return f"""
<div style="border-left:4px solid #FF9800;background:#fff8e1;padding:12px 16px;border-radius:4px;margin:8px 0">
  <strong>⚠ Out-of-Distribution — {model_name}</strong><br>
  Your text is unlike the data this model learned from. Treat these results as weak signals only.
</div>"""


def year_warning_banner(warning_text: str) -> str:
    return f"""
<div style="border-left:4px solid #FF9800;background:#fff8e1;padding:12px 16px;border-radius:4px;margin:8px 0">
  <strong>⚠ Temporal Distribution Warning</strong><br>
  {warning_text}
</div>"""


ASPECT_ICONS = {
    "evidence_found":     ("✅", "Evidence Found",    "#e8f5e9"),
    "partial":            ("🔶", "Partial Evidence",   "#fff8e1"),
    "not_stated":         ("⬜", "Not Stated",         "#f5f5f5"),
    "risk_signals_found": ("⚠",  "Risk Signal",        "#fff3e0"),
    "none_detected":      ("⬜", "None Detected",      "#f5f5f5"),
}

INTERP_ICONS = {
    "Elevated concern":              ("🔴", "#ffebee"),
    "Mixed picture":                 ("🟡", "#fffde7"),
    "Lower concern, under-evidenced":("🟢", "#e8f5e9"),
    "Insufficient basis":            ("⚪", "#f5f5f5"),
}

RISK_COLORS = {
    "Low":       "#4CAF50",
    "Moderate":  "#FFC107",
    "High":      "#FF5722",
    "Very High": "#B71C1C",
}

WORD_METER_CSS = {
    "red":   ("🔴", "Under 40 words — add more detail so the models have more to work with."),
    "amber": ("🟡", "40–80 words — more detail is always helpful."),
    "green": ("🟢", "Good detail level."),
}


def word_meter(text: str) -> tuple[str, str]:
    n = len(text.split())
    if n < 40:
        return WORD_METER_CSS["red"]
    elif n < 80:
        return WORD_METER_CSS["amber"]
    return WORD_METER_CSS["green"]

