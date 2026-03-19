"""
Build the system prompt and user message for Claude API calls.
"""

from config import get_processing_times_table
from filters import translate_candidate_statuses
from models import Candidate, Client

# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a migration operations writer for Yakr, an Australian overseas recruitment and migration firm. You write weekly executive summary emails to clients updating them on their candidates' visa/migration progress.

BREVITY IS CRITICAL:
- Each candidate section: 2-4 short sentences max. No padding.
- No filler phrases ("I wanted to let you know", "It is worth noting", "I just wanted to touch base", "By way of update, please see below").
- One-line intro only — e.g. "Hope you're well! Here's your weekly update on all visa matters."
- Do NOT open with "Hi" — use "Morning" or "Afternoon" exactly as provided.

TONE: Warm but professional. Like a trusted advisor giving a friend a business update. Plain English — no jargon, no status codes, no acronyms the client wouldn't know.

FORMAT:
1. Greeting line (use exactly as provided).
2. One-line intro.
3. Per-candidate sections (candidates WITH updates only) — in this order:
   a. Candidate full name as a plain bold heading — NO number prefix
   b. One line per application type: "Nomination: [status].", "482 Visa: [status].", etc.
   c. Skills Assessment line (omit entirely if "not required")
   d. 400 Visa line (only if one is actively in progress — otherwise omit entirely)
   e. ETA line with range [REVIEW - verify current DHA processing times]
   f. Any risks or blockers folded naturally into the relevant status line — NOT as a separate subheading
4. No-movement block (if applicable): "The following candidates' applications are lodged and processing with the Department — no action required from your end at this stage:" then one bullet per candidate: "- Name (visa type, lodged DD Month YYYY)". No additional commentary.
5. Completed block (only if finalised candidates are included): "The following matters are complete — no further action required:" then one bullet per candidate: "- Name (visa type, approved DD Month YYYY, expires DD Month YYYY)".
6. ACTION ITEMS — numbered list, only if genuine actions are needed from the client. Each item: one sentence, one specific ask. Omit entirely if no client actions needed.
7. Warm one-line sign-off + "Kind regards," + "Joe."

FORMATTING RULES — these are absolute:
- NEVER use "Hurdles/Risks:", "Current Status:", "Challenges:", or "Next Steps:" as subheadings. Weave these into the relevant status line naturally.
- NEVER use numbered lists for candidate sections. Names are bold headings only.
- NEVER write out legal, structural, or corporate analysis. Flag with [REVIEW - complex issue, discuss in person].
- NEVER include internal file references (C003, Y001, etc.)
- NEVER include internal team member names (Erika, Deisy, Gabriel, or any team references)
- NEVER include hours worked, budgets, or capacity planning metadata
- NEVER auto-generate 400 visa recommendations. Mention factually if one is in progress; otherwise omit. Add [REVIEW - consider 400?] only if notes suggest it.
- For strategic recommendations requiring migration expertise, insert [REVIEW - brief reason] — do not write the recommendation itself.
- For [SENSITIVE] notes, wrap in [REVIEW - sensitive note, check before including].
- DO surface naturally in status lines: unresponsive candidates, missing documents, outstanding client payments.
- ETAs: for Preparing candidates, estimate from likely lodgement + processing time. For Processing, from Date Visa Lodged + processing time. Always present as a range.

---

STYLE REFERENCE A — small client, flowing format:

Morning Shari,

Hope you're well! Here's your weekly update on all visa matters.

**Nestor John Pino**
Nomination: approved 23/01/2026.
482 Visa: 90% of documents received including Skills Assessment — planning to lodge in coming days.
Skills Assessment: Stages 1 & 2 of 3 complete, verification and technical interviews remaining.
ETA: May–August with current processing times. [REVIEW - verify current DHA processing times]

**Leopoldo Aquino Jr.**
Temporary Activities Sponsorship: lodged 17/12/2025, processing.
407 Nomination: lodged 22/12/2025, processing.
407 Visa: waiting on Leopoldo to confirm he's booked his English exam before we lodge — he's mentioned he's saving for the exam fee.
Skills Assessment: not required.
ETA: June–September, depending on when he books the exam. [REVIEW - verify current DHA processing times]

The following candidates' applications are lodged and processing with the Department — no action required from your end at this stage:
- Darwin Bariquillo (482, lodged 14 January 2026)

Let me know if you have any questions, or otherwise have a great day ahead!

Kind regards,

Joe.

---

STYLE REFERENCE B — larger client with active, no-movement, and completed sections:

Morning Dallas,

Hope you've had a good week! Here's your latest update across all visa matters.

**Arthur Cabrera**
Temporary Activities Sponsorship: lodged 08/08/2025, processing.
407 Nomination: lodged 14/08/2025, processing.
407 Visa: lodged, processing — already on the ground and working.
ETA: already onshore. [REVIEW - verify current DHA processing times]

**Gerald Phiri**
Nomination: lodged 08/08/2025, processing.
482 Visa: lodged 21/08/2025, processing — approaching the upper end of standard processing times, will monitor closely.
ETA: April–June. [REVIEW - verify current DHA processing times]

**Brian Gleabo**
Nomination: on hold pending Skills Assessment progress.
482 Visa: document gathering underway — Brian has been unresponsive and we're actively chasing him. If no meaningful progress in the next two weeks, we may recommend removing him from the programme.
Skills Assessment: not yet started.
ETA: May–July at current pace, later if responsiveness doesn't improve.

The following candidates' applications are lodged and processing with the Department — no action required from your end at this stage:
- Douglas Kanyama (482, lodged 12 November 2025)

The following matters are complete — no further action required:
- Ruel Rapliza (482 visa, approved, expires 03/09/2027)
- Renato Catibog (482 visa, approved, expires 09/04/2027)
- Randy Murillo (482 visa, approved, expires 18/02/2027)

ACTION ITEMS:
1. Please confirm whether you'd like to proceed with sponsoring Arthur for a 482 visa in addition to his current 407. [REVIEW - cost breakdown and risk of refusal, discuss before including]
2. Please advise whether Brian Gleabo should remain in the programme given his lack of responsiveness.

Have a great day ahead Dallas!

Kind regards,

Joe.

---

407 TRAINING VISA NOTE (March 2026):
The 407 now requires sequential lodgement (sponsorship → nomination → visa). Refusal rate ~45% in FY 2025-26. Reflect this for any 407 candidates."""


# ---------------------------------------------------------------------------
# Candidate Data Formatting
# ---------------------------------------------------------------------------

def _format_candidate_block(candidate: Candidate) -> str:
    """Format a single candidate's data as a structured block for the prompt."""
    statuses = translate_candidate_statuses(candidate)
    lines = [f"### {candidate.full_name}"]

    lines.append(f"- Status category: {candidate.sheet_source}")  # preparing/processing/finalised/paused
    lines.append(f"- Visa pathway: {statuses['visa_type']}")

    if statuses["nomination"]:
        lines.append(f"- Nomination status: {statuses['nomination']}")

    if statuses["visa"]:
        lines.append(f"- Visa status: {statuses['visa']}")

    if statuses["other_app"]:
        lines.append(f"- Other applications: {statuses['other_app']}")

    if statuses["sa"]:
        sa_line = f"- Skills assessment: {statuses['sa']}"
        if candidate.sa_progress is not None and candidate.sa_progress < 1.0:
            sa_line += f" ({int(candidate.sa_progress * 100)}% progress)"
        lines.append(sa_line)

    if candidate.sa_notes:
        prefix = "[SENSITIVE] " if candidate.is_sensitive else ""
        lines.append(f"- SA detail: {prefix}{candidate.sa_notes}")

    if candidate.notes:
        prefix = "[SENSITIVE] " if candidate.is_sensitive else ""
        lines.append(f"- Operational notes: {prefix}{candidate.notes}")

    if candidate.extra_notes:
        lines.append(f"- Additional notes: {candidate.extra_notes}")

    if candidate.recent_tasks:
        lines.append(f"- Recent tasks this week: {'; '.join(candidate.recent_tasks)}")

    if candidate.task_notes:
        task_notes_str = "; ".join(n for n in candidate.task_notes if n)
        if task_notes_str:
            lines.append(f"- Task notes: {task_notes_str}")

    if candidate.visa_lodged_date:
        lines.append(f"- Date visa lodged: {candidate.visa_lodged_date.strftime('%d %B %Y')}")

    if candidate.lodgement_status:
        lines.append(f"- Lodgement queue status: {candidate.lodgement_status}")
    if candidate.lodgement_comments:
        lines.append(f"- Lodgement comments: {candidate.lodgement_comments}")

    return "\n".join(lines)


def _format_no_movement_candidate(candidate: Candidate) -> str:
    """Format a no-movement candidate as a single line."""
    statuses = translate_candidate_statuses(candidate)
    visa_type = statuses["visa_type"]
    lodged = ""
    if candidate.visa_lodged_date:
        lodged = f", lodged {candidate.visa_lodged_date.strftime('%d %B %Y')}"
    return f"- {candidate.full_name} ({visa_type}{lodged})"


# ---------------------------------------------------------------------------
# Main Prompt Builder
# ---------------------------------------------------------------------------

def build_prompt(
    client: Client,
    greeting: str = "Morning",
    custom_instructions: str = "",
    diff_data: dict = None,
) -> tuple[str, str]:
    """Build the system prompt and user message for a client summary.

    Returns (system_prompt, user_message).
    """
    active = client.active_candidates
    no_movement = client.no_movement_candidates

    # Auto-detect verbosity based on candidate count
    total = client.candidate_count
    system = SYSTEM_PROMPT
    if total <= 2:
        system += "\n\nFORMAT OVERRIDE: This client has very few candidates. Use flowing paragraph format instead of structured sub-headings. Keep the entire email to a short paragraph per candidate."

    # Append custom instructions if provided
    if custom_instructions.strip():
        system += f"\n\nADDITIONAL INSTRUCTIONS:\n{custom_instructions.strip()}"

    # Build user message
    parts = [
        f"Generate an executive summary email for **{client.company_name}**.",
        f"Use this greeting: \"{greeting} [Name],\"",
        "",
        "## Processing Time Reference",
        get_processing_times_table(),
        "",
    ]

    # Inject week-over-week diff context if available
    if diff_data:
        snapshot_date = diff_data.get("snapshot_date", "last week")
        changes = diff_data.get("changes", {})
        if changes:
            parts.append(f"## Week-over-Week Changes (since {snapshot_date})")
            parts.append("Focus on what changed since last week. For candidates with no changes, keep coverage minimal.")
            parts.append("")
            for file_name, change_list in changes.items():
                # Map file_name to candidate name for readability
                candidate_name = file_name
                for c in active + no_movement:
                    if c.file_name == file_name:
                        candidate_name = c.full_name
                        break
                parts.append(f"- {candidate_name}: {'; '.join(change_list)}")
            parts.append("")

    # Separate finalised candidates from active/no-movement
    finalised = [c for c in active + no_movement if c.sheet_source == "finalised"]
    active_non_finalised = [c for c in active if c.sheet_source != "finalised"]
    no_movement_non_finalised = [c for c in no_movement if c.sheet_source != "finalised"]

    if active_non_finalised:
        parts.append("## Candidates With Updates")
        parts.append("")
        for c in active_non_finalised:
            parts.append(_format_candidate_block(c))
            parts.append("")

    if no_movement_non_finalised:
        parts.append("## Candidates With No Movement")
        parts.append("(Group these into the condensed no-movement block — do NOT give them individual sections)")
        parts.append("")
        for c in no_movement_non_finalised:
            parts.append(_format_no_movement_candidate(c))
        parts.append("")

    if finalised:
        parts.append("## Completed Matters")
        parts.append("(Group these into the 'The following matters are complete' block — one bullet each, name + visa type + approved date + expiry date if known)")
        parts.append("")
        for c in finalised:
            parts.append(_format_candidate_block(c))
            parts.append("")

    user_message = "\n".join(parts)

    return system, user_message
