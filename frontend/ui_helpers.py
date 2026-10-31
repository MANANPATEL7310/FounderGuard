"""Shared UI helpers used across all pages."""
from __future__ import annotations


# ── Status/warning banner helpers ─────────────────────────────────────────────

def not_applicable_card(model_name: str, reason: str) -> str:
    return f"""
<div style="border-left:4px solid #64748B;background:#F8FAFC;padding:14px 18px;border-radius:6px;margin:10px 0;border-top:1px solid #E2E8F0;border-right:1px solid #E2E8F0;border-bottom:1px solid #E2E8F0;">
  <strong style="color:#1E293B;font-size:0.95rem;">Notice — {model_name}: Not Applicable</strong><br>
  <span style="color:#475569;font-size:0.88rem;display:inline-block;margin-top:4px;">{reason}</span>
</div>"""


def error_card(model_name: str, reason: str) -> str:
    return f"""
<div style="border-left:4px solid #DC2626;background:#FEF2F2;padding:14px 18px;border-radius:6px;margin:10px 0;border-top:1px solid #FEE2E2;border-right:1px solid #FEE2E2;border-bottom:1px solid #FEE2E2;">
  <strong style="color:#991B1B;font-size:0.95rem;">Notice — {model_name}: Unavailable</strong><br>
  <span style="color:#B91C1C;font-size:0.88rem;display:inline-block;margin-top:4px;">{reason}</span>
</div>"""


def ood_banner(model_name: str) -> str:
    return f"""
<div style="border-left:4px solid #D97706;background:#FFFBEB;padding:14px 18px;border-radius:6px;margin:10px 0;border-top:1px solid #FEF3C7;border-right:1px solid #FEF3C7;border-bottom:1px solid #FEF3C7;">
  <strong style="color:#92400E;font-size:0.95rem;">Out-of-Distribution Warning — {model_name}</strong><br>
  <span style="color:#B45309;font-size:0.88rem;display:inline-block;margin-top:4px;">Your text is unlike the historical training data. Treat these results as weak signals only.</span>
</div>"""


def year_warning_banner(warning_text: str) -> str:
    return f"""
<div style="border-left:4px solid #D97706;background:#FFFBEB;padding:14px 18px;border-radius:6px;margin:10px 0;border-top:1px solid #FEF3C7;border-right:1px solid #FEF3C7;border-bottom:1px solid #FEF3C7;">
  <strong style="color:#92400E;font-size:0.95rem;">Temporal Distribution Warning</strong><br>
  <span style="color:#B45309;font-size:0.88rem;display:inline-block;margin-top:4px;">{warning_text}</span>
</div>"""


ASPECT_ICONS = {
    "evidence_found":     ("[Found]",    "Evidence Found",    "#F0FDF4"),
    "partial":            ("[Partial]",  "Partial Evidence",   "#FFFBEB"),
    "not_stated":         ("[Unstated]", "Not Stated",         "#F8FAFC"),
    "risk_signals_found": ("[Risk]",     "Risk Signal",        "#FEF2F2"),
    "none_detected":      ("[None]",     "None Detected",      "#F8FAFC"),
}

INTERP_ICONS = {
    "Elevated concern":              ("[Elevated]",  "#FEF2F2"),
    "Mixed picture":                 ("[Mixed]",     "#FFFBEB"),
    "Lower concern, under-evidenced":("[Low]",       "#F0FDF4"),
    "Insufficient basis":            ("[Baseline]",  "#F8FAFC"),
}

RISK_COLORS = {
    "Low":       "#16A34A",
    "Moderate":  "#D97706",
    "High":      "#EA580C",
    "Very High": "#DC2626",
}

WORD_METER_CSS = {
    "red":   ("[Short]", "Under 40 words — add more detail so the models have more to work with."),
    "amber": ("[Medium]", "40–80 words — more detail is always helpful."),
    "green": ("[Good]", "Good detail level."),
}


def word_meter(text: str) -> tuple[str, str]:
    n = len(text.split())
    if n < 40:
        return WORD_METER_CSS["red"]
    elif n < 80:
        return WORD_METER_CSS["amber"]
    return WORD_METER_CSS["green"]
