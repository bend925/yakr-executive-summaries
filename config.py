"""
Configuration: status translation maps, processing times, multi-branch mappings,
sensitive content patterns, and credential blacklists.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Status Translation Maps — raw codes → plain English
# ---------------------------------------------------------------------------

NOMINATION_STATUS_MAP = {
    # 482
    "482Nom_Not_Drafted": "not yet started",
    "482Nom_Drafted_Not_Ready": "drafted, not ready — awaiting missing documents",
    "482Nom_Drafted_Ready": "drafted, ready to lodge",
    "482Nom_Processing": "lodged, processing",
    "482Nom_Approved": "approved",
    "482NTransfer_Processing": "nomination transfer lodged, processing",
    "482NTransfer_Approved": "nomination transfer approved",
    # 186
    "186Nom_Not_Drafted": "not yet started",
    "186Nom_Drafted_Not_Ready": "drafted, not ready — awaiting missing documents",
    "186Nom_Drafted_Ready": "drafted, ready to lodge",
    "186Nom_Processing": "lodged, processing",
    "186Nom_Approved": "approved",
    # 407
    "407Nom_Not_Drafted": "not yet started",
    "407Nom_Drafted_Not_Ready": "drafted, not ready — awaiting missing documents",
    "407Nom_Drafted_Ready": "drafted, ready to lodge",
    "407Nom_Processing": "lodged, processing",
    "407Nom_Approved": "approved",
    # General
    "Not_Applicable": None,
}

VISA_STATUS_MAP = {
    # 482
    "482Visa_Not_Drafted": "not yet started",
    "482Visa_Drafted_Not_Ready": "drafted, not ready — awaiting missing documents",
    "482Visa_Drafted_Ready": "drafted, ready to lodge",
    "482Visa_AwaitingPayment": "lodged, awaiting payment from client",
    "482Visa_Processing": "lodged, processing",
    "482Visa_Approved": "approved",
    # 186
    "186Visa_Not_Drafted": "not yet started",
    "186Visa_Drafted_Not_Ready": "drafted, not ready — awaiting missing documents",
    "186Visa_Drafted_Ready": "drafted, ready to lodge",
    "186Visa_AwaitingPayment": "lodged, awaiting payment from client",
    "186Visa_Processing": "lodged, processing",
    "186Visa_Approved": "approved",
    # 407
    "407Visa_Not_Drafted": "not yet started",
    "407Visa_Drafted_Not_Ready": "drafted, not ready — awaiting missing documents",
    "407Visa_Drafted_Ready": "drafted, ready to lodge",
    "407Visa_AwaitingPayment": "lodged, awaiting payment from client",
    "407Visa_Processing": "lodged, processing",
    "407Visa_Approved": "approved",
    # 400
    "400Visa_Not_Drafted": "not yet started",
    "400Visa_Drafted": "drafted",
    "400Visa_Drafted_Not_Ready": "drafted, not ready — awaiting missing documents",
    "400Visa_Drafted_Ready": "drafted, ready to lodge",
    "400Visa_Processing": "lodged, processing",
    "400Visa_Approved": "approved",
    # Subsequent entrant
    "482SubEntVisa_Not_Drafted": "subsequent entrant visa not yet started",
    "482SubEntVisa_Drafted_Not_Ready": "subsequent entrant visa drafted, not ready",
    "482SubEntVisa_Drafted_Ready": "subsequent entrant visa drafted, ready to lodge",
    "482SubEntVisa_Processing": "subsequent entrant visa lodged, processing",
    "482SubEntVisa_Approved": "subsequent entrant visa approved",
    # Partner visa
    "820-801Visa_Processing": "partner visa lodged, processing",
    "820Visa_Processing": "partner visa lodged, processing",
    # General
    "Not_Applicable": None,
}

OTHER_APP_STATUS_MAP = {
    # 400
    "400Visa_Not_Drafted": "400 visa not yet started",
    "400Visa_Drafted_Not_Ready": "400 visa drafted, not ready",
    "400Visa_Drafted_Ready": "400 visa drafted, ready to lodge",
    "400Visa_Processing": "400 visa lodged, processing",
    "400Visa_Approved": "400 visa approved",
    "400_Approved": "400 visa approved",
    # SBS
    "SBS_Not_Drafted": "Standard Business Sponsorship not yet started",
    "SBS_Drafted_Not_Ready": "Standard Business Sponsorship drafted, not ready",
    "SBS_Drafted_Ready": "Standard Business Sponsorship drafted, ready to lodge",
    "SBS_Processing": "Standard Business Sponsorship lodged, processing",
    "SBS_Approved": "Standard Business Sponsorship approved",
    # TAS
    "TAS_Not_Drafted": "Temporary Activities Sponsorship not yet started",
    "TAS_Drafted_Not_Ready": "Temporary Activities Sponsorship drafted, not ready",
    "TAS_Drafted_Ready": "Temporary Activities Sponsorship drafted, ready to lodge",
    "TAS_Processing": "Temporary Activities Sponsorship lodged, processing",
    "TAS_Approved": "Temporary Activities Sponsorship approved",
    # General
    "Not_Applicable": None,
}

SA_STATUS_MAP = {
    "SA_Unstarted": "not yet started",
    "SA_LoginCreated": "account created, not yet progressing",
    "SA_Stage1": "on Stage 1 of 3",
    "SA_Stage2": "on Stage 2 of 3",
    "SA_Stage3": "on Stage 3 of 3",
    "SA_TechnicalInterview": "technical interview stage",
    "SA_Completed": "completed",
    "Not_Required": "not required",
    "Not_Applicable": None,
}

VISA_TYPE_MAP = {
    "482Nom-Visa": "482 skilled worker visa",
    "186Nom-Visa": "186 permanent residency visa",
    "407Nom-Visa": "407 training visa",
    "400Visa_482Nom-Visa": "400 short-stay visa, then 482 skilled worker visa",
    "482SubEntVisa": "482 subsequent entrant visa (family member)",
    "482NTransfer": "482 nomination transfer",
}


def translate_status(raw: str | None, status_map: dict) -> str | None:
    """Translate a raw status code to plain English. Returns None if N/A."""
    if not raw:
        return None
    raw = raw.strip()
    if raw in status_map:
        return status_map[raw]
    # Fallback: return the raw code wrapped in a review tag
    return f"{raw} [REVIEW - unknown status code]"


# ---------------------------------------------------------------------------
# Processing Time Reference Table (as at March 2026)
# ---------------------------------------------------------------------------

# (min_months, max_months) for 50th and 90th percentile ranges
PROCESSING_TIMES = {
    "400": {
        "description": "Subclass 400 (Temporary Work - Short Stay)",
        "range_50": (0.5, 0.75),   # 2-3 weeks
        "range_90": (0.75, 1.0),   # 3-4 weeks
    },
    "407": {
        "description": "Subclass 407 (Training Visa)",
        "range_50": (3, 5),
        "range_90": (9, 12),
    },
    "482_nom": {
        "description": "Subclass 482 (Skills in Demand) — Nomination",
        "range_50": (4, 4),
        "range_90": (7, 7),
    },
    "482_visa": {
        "description": "Subclass 482 (Skills in Demand) — Visa",
        "range_50": (4, 4),
        "range_90": (7, 7),
    },
    "186_de": {
        "description": "Subclass 186 (ENS) — Direct Entry",
        "range_50": (12, 12),
        "range_90": (18, 19),
    },
    "186_trt": {
        "description": "Subclass 186 (ENS) — Temporary Residence Transition",
        "range_50": (13, 14),
        "range_90": (18, 20),
    },
}


def get_processing_times_table() -> str:
    """Format the processing times as a readable reference table for the LLM prompt."""
    lines = ["| Visa Type | 50% processed in | 90% processed in |",
             "|---|---|---|"]
    for key, info in PROCESSING_TIMES.items():
        r50 = info["range_50"]
        r90 = info["range_90"]

        def fmt_val(v):
            if v < 1:
                return f"{int(v * 4)} weeks"
            if v == int(v):
                return f"{int(v)} months"
            return f"{v} months"

        def fmt(r):
            if r[0] == r[1]:
                return f"~{fmt_val(r[0])}"
            return f"{fmt_val(r[0])} – {fmt_val(r[1])}"

        lines.append(f"| {info['description']} | {fmt(r50)} | {fmt(r90)} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Multi-Branch Client Mappings
# ---------------------------------------------------------------------------

MULTI_BRANCH_PREFIXES = {
    "Pickerings": ["Pickerings", "PMG"],
    "Calibre": ["Calibre"],
}


def detect_parent_company(company: str) -> str | None:
    """Return the parent company name if this company is a branch, else None."""
    company_clean = company.strip()
    for parent, prefixes in MULTI_BRANCH_PREFIXES.items():
        for prefix in prefixes:
            if company_clean.startswith(prefix):
                return parent
    return None


def detect_branch_name(company: str, parent: str) -> str | None:
    """Extract the branch name from a company string given its parent."""
    company_clean = company.strip()
    for prefix in MULTI_BRANCH_PREFIXES.get(parent, []):
        if company_clean.startswith(prefix):
            branch = company_clean[len(prefix):].strip()
            return branch if branch else company_clean
    return company_clean


# ---------------------------------------------------------------------------
# Sensitive Content Patterns
# ---------------------------------------------------------------------------

SENSITIVE_PATTERNS = [
    re.compile(r"\bfraud\b", re.IGNORECASE),
    re.compile(r"\bforg(e|ed|ery|ing)\b", re.IGNORECASE),
    re.compile(r"\bintegrity\b", re.IGNORECASE),
    re.compile(r"\bdisciplin(e|ed|ary)\b", re.IGNORECASE),
    re.compile(r"\b(fired|terminated|dismissal)\b", re.IGNORECASE),
    re.compile(r"\bcan'?t afford\b", re.IGNORECASE),
    re.compile(r"\bfinancial difficult", re.IGNORECASE),
    re.compile(r"\bdisagree(ment|d)?\b", re.IGNORECASE),
    re.compile(r"\bdispute\b", re.IGNORECASE),
    re.compile(r"\babscond", re.IGNORECASE),
    re.compile(r"\bdeport(ation|ed)?\b", re.IGNORECASE),
    re.compile(r"\billegal\b", re.IGNORECASE),
    re.compile(r"\bcancel(led)?\b.*\b(application|enrollment|enrolment)\b", re.IGNORECASE),
]

# Internal team member names to strip from notes
INTERNAL_TEAM_NAMES = ["Erika", "Deisy", "Gabriel", "Joe", "JH", "AP"]

# Columns to never read from Skills Assessment sheets
SA_CREDENTIAL_COLUMNS = {"Email", "Password", "TRA Username", "TRA"}

# Sheets to skip entirely
SKIP_SHEETS = {"Group Stats", "Stats", "LMT"}
