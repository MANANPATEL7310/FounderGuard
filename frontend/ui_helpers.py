"""Shared UI helpers used across all pages."""
from __future__ import annotations


# ── Status/warning banner helpers ─────────────────────────────────────────────

def not_applicable_card(model_name: str, reason: str) -> str:
    return f"""
<div style="border-left:4px solid #64748B;background:rgba(100,116,139,0.12);padding:14px 18px;border-radius:8px;margin:10px 0;border:1px solid rgba(100,116,139,0.25);">
  <strong style="color:#94A3B8;font-size:0.95rem;">⊘ {model_name}: Not Applicable</strong><br>
  <span style="color:#CBD5E1;font-size:0.88rem;display:inline-block;margin-top:4px;">{reason}</span>
</div>"""


def error_card(model_name: str, reason: str) -> str:
    return f"""
<div style="border-left:4px solid #EF4444;background:rgba(239,68,68,0.12);padding:14px 18px;border-radius:8px;margin:10px 0;border:1px solid rgba(239,68,68,0.25);">
  <strong style="color:#F87171;font-size:0.95rem;">✕ {model_name}: Unavailable</strong><br>
  <span style="color:#FECACA;font-size:0.88rem;display:inline-block;margin-top:4px;">{reason}</span>
</div>"""


def ood_banner(model_name: str) -> str:
    return f"""
<div style="border-left:4px solid #F59E0B;background:rgba(245,158,11,0.12);padding:14px 18px;border-radius:8px;margin:10px 0;border:1px solid rgba(245,158,11,0.25);">
  <strong style="color:#FBBF24;font-size:0.95rem;">⚠ Out-of-Distribution — {model_name}</strong><br>
  <span style="color:#FDE68A;font-size:0.88rem;display:inline-block;margin-top:4px;">Your text is unlike the data this model learned from. Treat these results as weak signals only.</span>
</div>"""


def year_warning_banner(warning_text: str) -> str:
    return f"""
<div style="border-left:4px solid #F59E0B;background:rgba(245,158,11,0.12);padding:14px 18px;border-radius:8px;margin:10px 0;border:1px solid rgba(245,158,11,0.25);">
  <strong style="color:#FBBF24;font-size:0.95rem;">⚠ Temporal Distribution Warning</strong><br>
  <span style="color:#FDE68A;font-size:0.88rem;display:inline-block;margin-top:4px;">{warning_text}</span>
</div>"""


ASPECT_ICONS = {
    "evidence_found":     ("✅", "Evidence Found",    "rgba(16,185,129,0.15)"),
    "partial":            ("🔶", "Partial Evidence",   "rgba(245,158,11,0.15)"),
    "not_stated":         ("⬜", "Not Stated",         "rgba(100,116,139,0.12)"),
    "risk_signals_found": ("⚠",  "Risk Signal",        "rgba(239,68,68,0.15)"),
    "none_detected":      ("⬜", "None Detected",      "rgba(100,116,139,0.12)"),
}

INTERP_ICONS = {
    "Elevated concern":              ("🔴", "rgba(239,68,68,0.15)"),
    "Mixed picture":                 ("🟡", "rgba(245,158,11,0.15)"),
    "Lower concern, under-evidenced":("🟢", "rgba(16,185,129,0.15)"),
    "Insufficient basis":            ("⚪", "rgba(100,116,139,0.15)"),
}

RISK_COLORS = {
    "Low":       "#10B981",
    "Moderate":  "#F59E0B",
    "High":      "#F97316",
    "Very High": "#EF4444",
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
