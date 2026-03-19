"""
Week-over-week diff engine for candidate data.
Builds snapshots of parsed candidate data and compares them to detect changes.
"""

import hashlib
import json
from datetime import date, datetime
from typing import Optional

from models import Candidate


def build_snapshot(candidates: list[Candidate]) -> dict:
    """Serialize parsed candidates into a JSON-safe snapshot dict.

    The snapshot is keyed by file_name and stores comparable fields.
    A top-level 'snapshot_date' records when it was created.
    """
    snapshot = {
        "snapshot_date": date.today().isoformat(),
        "candidates": {},
    }

    for c in candidates:
        # Hash notes to detect changes without storing full text
        notes_text = f"{c.notes or ''}|{c.extra_notes or ''}"
        notes_hash = hashlib.sha256(notes_text.encode()).hexdigest()[:16]

        snapshot["candidates"][c.file_name] = {
            "given_names": c.given_names,
            "family_names": c.family_names,
            "company": c.company,
            "nomination_status": c.nomination_status or "",
            "visa_status": c.visa_status or "",
            "other_app_status": c.other_app_status or "",
            "sa_status": c.sa_status or "",
            "sa_progress": c.sa_progress,
            "visa_lodged_date": c.visa_lodged_date.isoformat() if c.visa_lodged_date else None,
            "sheet_source": c.sheet_source or "",
            "notes_hash": notes_hash,
            "recent_tasks": list(c.recent_tasks) if c.recent_tasks else [],
            "lodgement_status": c.lodgement_status or "",
        }

    return snapshot


def diff_snapshots(previous: dict, current: dict) -> dict:
    """Compare two snapshots and return per-candidate change descriptions.

    Returns:
        {
            "snapshot_date": "2026-03-12",  # date of previous snapshot
            "changes": {
                "C003": ["Nomination status changed from 'processing' to 'approved'", ...],
                "Y001": ["New candidate"],
                ...
            },
            "summary": {"changed": 5, "new": 2, "unchanged": 10, "removed": 1}
        }
    """
    prev_candidates = previous.get("candidates", {})
    curr_candidates = current.get("candidates", {})

    changes = {}
    changed_count = 0
    new_count = 0
    unchanged_count = 0
    removed_count = 0

    # Check current candidates against previous
    for file_name, curr in curr_candidates.items():
        if file_name not in prev_candidates:
            changes[file_name] = ["New candidate (not in last week's data)"]
            new_count += 1
            continue

        prev = prev_candidates[file_name]
        candidate_changes = []

        # Status transitions
        if prev["nomination_status"] != curr["nomination_status"]:
            candidate_changes.append(
                f"Nomination status changed from '{prev['nomination_status']}' to '{curr['nomination_status']}'"
            )

        if prev["visa_status"] != curr["visa_status"]:
            candidate_changes.append(
                f"Visa status changed from '{prev['visa_status']}' to '{curr['visa_status']}'"
            )

        if prev["other_app_status"] != curr["other_app_status"]:
            candidate_changes.append(
                f"Other application status changed from '{prev['other_app_status']}' to '{curr['other_app_status']}'"
            )

        if prev["sa_status"] != curr["sa_status"]:
            candidate_changes.append(
                f"Skills assessment changed from '{prev['sa_status']}' to '{curr['sa_status']}'"
            )

        # SA progress
        if prev["sa_progress"] != curr["sa_progress"]:
            if curr["sa_progress"] is not None:
                candidate_changes.append(
                    f"SA progress updated to {int(curr['sa_progress'] * 100)}%"
                )

        # Sheet source change (e.g. Preparing → Processing)
        if prev["sheet_source"] != curr["sheet_source"]:
            candidate_changes.append(
                f"Moved from {prev['sheet_source'].title()} to {curr['sheet_source'].title()}"
            )

        # Visa lodged date
        if prev["visa_lodged_date"] != curr["visa_lodged_date"] and curr["visa_lodged_date"]:
            candidate_changes.append(
                f"Visa lodged on {curr['visa_lodged_date']}"
            )

        # Notes changed (via hash comparison)
        if prev["notes_hash"] != curr["notes_hash"]:
            candidate_changes.append("Notes updated (new information added)")

        # New tasks this week
        prev_tasks = set(prev.get("recent_tasks", []))
        curr_tasks = set(curr.get("recent_tasks", []))
        new_tasks = curr_tasks - prev_tasks
        if new_tasks:
            candidate_changes.append("New activity this week")

        # Lodgement status
        if prev["lodgement_status"] != curr["lodgement_status"]:
            candidate_changes.append(
                f"Lodgement status changed to '{curr['lodgement_status']}'"
            )

        if candidate_changes:
            changes[file_name] = candidate_changes
            changed_count += 1
        else:
            unchanged_count += 1

    # Check for removed candidates
    for file_name in prev_candidates:
        if file_name not in curr_candidates:
            changes[file_name] = ["Candidate removed (no longer in data)"]
            removed_count += 1

    return {
        "snapshot_date": previous.get("snapshot_date", "unknown"),
        "changes": changes,
        "summary": {
            "changed": changed_count,
            "new": new_count,
            "unchanged": unchanged_count,
            "removed": removed_count,
        },
    }


def summarise_diff(diff_result: dict) -> dict:
    """Extract the summary counts from a diff result."""
    return diff_result.get("summary", {
        "changed": 0, "new": 0, "unchanged": 0, "removed": 0,
    })


def snapshot_to_json(snapshot: dict) -> str:
    """Serialize a snapshot to a JSON string."""
    return json.dumps(snapshot, indent=2, default=str)


def json_to_snapshot(json_str: str) -> Optional[dict]:
    """Deserialize a JSON string to a snapshot dict. Returns None on error."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None
