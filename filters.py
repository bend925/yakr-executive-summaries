"""
Content filtering: sensitive note detection, movement classification,
status translation, and internal data stripping.
"""

import re

from config import (
    INTERNAL_TEAM_NAMES,
    NOMINATION_STATUS_MAP,
    OTHER_APP_STATUS_MAP,
    SA_STATUS_MAP,
    SENSITIVE_PATTERNS,
    VISA_STATUS_MAP,
    VISA_TYPE_MAP,
    translate_status,
)
from models import Candidate


def check_sensitive(text: str) -> bool:
    """Return True if the text matches any sensitive content pattern."""
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            return True
    return False


def strip_internal_names(text: str) -> str:
    """Remove internal team member name references from notes."""
    result = text
    for name in INTERNAL_TEAM_NAMES:
        # Remove patterns like "Erika:", "JH,", "AP:" etc.
        result = re.sub(rf'\b{re.escape(name)}\b\s*[,:;]?\s*', '', result)
    # Clean up leftover artefacts
    result = re.sub(r'\s{2,}', ' ', result)
    return result.strip()


def classify_movement(candidate: Candidate) -> bool:
    """Determine if a candidate has meaningful movement/updates.
    Returns True if there's something to report, False for 'no movement'."""
    # Only Processing sheet candidates can be "no movement"
    if candidate.sheet_source != "processing":
        return True

    # Check if statuses indicate active processing (standard state)
    nom = candidate.nomination_status or ""
    visa = candidate.visa_status or ""

    if "Processing" not in nom and "Processing" not in visa:
        return True  # non-standard status = something to report

    # Check if notes indicate anything beyond standard processing
    notes_lower = (candidate.notes or "").lower().strip()
    generic_phrases = [
        "lodged, processing, no further action needed",
        "lodged, processing",
        "no further action needed",
        "processing, no action required",
        "",
    ]
    if notes_lower not in generic_phrases:
        return True

    # Check for recent capacity planning activity
    if candidate.recent_tasks:
        return True

    # No movement
    return False


def filter_candidate(candidate: Candidate) -> Candidate:
    """Apply all content filters to a candidate in-place and return it.

    - Classifies movement
    - Detects sensitive content
    - Strips internal team names from notes
    """
    # Movement classification
    candidate.has_movement = classify_movement(candidate)

    # Check all text fields for sensitive content
    all_text = " ".join([
        candidate.notes,
        candidate.extra_notes,
        candidate.sa_notes,
        " ".join(candidate.task_notes),
    ])
    candidate.is_sensitive = check_sensitive(all_text)

    # Strip internal team names from all note fields
    candidate.notes = strip_internal_names(candidate.notes)
    candidate.extra_notes = strip_internal_names(candidate.extra_notes)
    candidate.sa_notes = strip_internal_names(candidate.sa_notes)
    candidate.task_notes = [strip_internal_names(n) for n in candidate.task_notes]

    return candidate


def translate_candidate_statuses(candidate: Candidate) -> dict:
    """Translate all raw status codes to plain English. Returns a dict for prompt use."""
    return {
        "nomination": translate_status(candidate.nomination_status, NOMINATION_STATUS_MAP),
        "visa": translate_status(candidate.visa_status, VISA_STATUS_MAP),
        "other_app": translate_status(candidate.other_app_status, OTHER_APP_STATUS_MAP),
        "sa": translate_status(candidate.sa_status, SA_STATUS_MAP),
        "visa_type": VISA_TYPE_MAP.get(candidate.visa_type, candidate.visa_type),
    }


def filter_all_candidates(candidates: list[Candidate]) -> list[Candidate]:
    """Apply filters to all candidates."""
    return [filter_candidate(c) for c in candidates]
