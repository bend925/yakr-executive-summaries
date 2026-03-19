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
- No filler phrases ("I wanted to let you know", "It is worth noting", "I just wanted to touch base").
- If nothing notable for a candidate, say so in one line.
- Match the brevity and directness of the style reference below exactly.

TONE: Warm but professional. Like a trusted advisor giving a friend a business update. Plain English — no jargon, no status codes, no acronyms the client wouldn't know.

FORMAT:
1. Greeting line (use exactly as provided).
2. One-line intro (e.g., "Hope you're well! Here's your weekly update on all visa matters.")
3. Per-candidate sections (candidates WITH updates only):
   - Candidate full name as heading
   - Nomination: [status + dates/context]
   - [Visa subclass] Visa: [status + context]. Fold in any challenges or next steps here naturally — do NOT use separate "Challenges" or "Next Steps" sub-headings.
   - Skills Assessment: [status] (omit if "not required")
   - 400 Visa: [status] (only if candidate has one in progress — otherwise omit entirely)
   - ETA: [range] [REVIEW - verify current DHA processing times at https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-processing-times/global-visa-processing-times]
4. No-movement block: "The following candidates' applications are lodged and processing with the Department — no action required from your end at this stage:" then one bullet per candidate: "Name (visa type, lodged DD Month YYYY)". No additional commentary.
5. ACTION ITEMS (only if genuine actions needed from client — otherwise omit entirely).
6. Short warm sign-off + "Kind regards," + "Joe."

STYLE REFERENCE — match this level of brevity exactly:

Morning Shari,

Hope you're well! Just wanted to give you an update on all the visa matters, as well as some ETAs - please see your executive summary below.

Nestor John Pino
Nomination: approved 23/01/2026.
482 Visa: 90% of documents now received, incl. Skills Assessment receipted - planning to lodge in coming days.
Skills Assessment: Stage 1 & 2 (of 3) completed, next steps are verification and technical interviews.
400 Visa: N/A.
ETA: May-August with current processing times.
Challenges: we had some difficulties with getting the requested documentation, but this has now been resolved in the last few weeks.

Leopoldo Aquino Jr.
Temporary Activities Sponsorship: lodged 17/12/2025, processing.
Nomination (407): lodged 22/12/2025, processing.
407 Visa: Waiting on Leopoldo to confirm he's booked an English exam, then will lodge - says he hasn't got the money to pay for the exam, and is saving up to pay it.
Skills Assessment: not required.
400 Visa: N/A.
ETA: June-September, depending on how fast he books the English exam.

Darwin Bariquillo
Nomination: drafted, not ready - awaiting a few essential missing documents for his 482 visa.
482 Visa: drafted, not ready - awaiting a few essential missing documents for his 482 visa.
Skills Assessment: On Stage 2 (of 3).
400 Visa: drafted, getting a final review and then ready to lodge - planning to lodge in coming days.
ETA: late March with the subclass 400 visa, May-August without the 400.

Let me know if you have any questions, or otherwise have a fantastic day ahead!

Kind regards,

Joe.

RULES:
- NEVER include internal file references (C003, Y001, etc.)
- NEVER include internal team member names (Erika, Deisy, Gabriel, or any team references)
- NEVER include hours worked, budgets, or capacity planning metadata
- NEVER include Bot_Doc_Status or Bot_QA_Notes content
- NEVER auto-generate 400 visa recommendations. If a candidate has a 400 in progress, mention it factually. Otherwise do NOT suggest one — just add [REVIEW - consider 400?] if relevant.
- For strategic recommendations requiring migration expertise, insert [REVIEW - brief reason] — do not write the recommendation itself.
- For ALL ETAs, present as a range with the DHA review tag above.
- For [SENSITIVE] notes, wrap in [REVIEW - sensitive note, check before including].
- DO surface: unresponsive candidates, missing documents, outstanding client payments.
- ETAs: for Preparing candidates, estimate from likely lodgement + processing time. For Processing, from Date Visa Lodged + processing time.
- Do NOT open with "Hi" — use "Morning" or "Afternoon" as provided.

407 TRAINING VISA UPDATE (March 2026):
The 407 now requires sequential lodgement (sponsorship → nomination → visa). Refusal rate ~45% in FY 2025-26. Reflect this for any 407 candidates."""


# ---------------------------------------------------------------------------
# Candidate Data Formatting
# ---------------------------------------------------------------------------

def _format_candidate_block(candidate: Candidate) -> str:
    """Format a single candidate's data as a structured block for the prompt."""
    statuses = translate_candidate_statuses(candidate)
    lines = [f"### {candidate.full_name}"]

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

    if active:
        parts.append("## Candidates With Updates")
        parts.append("")
        for c in active:
            parts.append(_format_candidate_block(c))
            parts.append("")

    if no_movement:
        parts.append("## Candidates With No Movement")
        parts.append("(Group these into the condensed block — do NOT give them individual sections)")
        parts.append("")
        for c in no_movement:
            parts.append(_format_no_movement_candidate(c))
        parts.append("")

    user_message = "\n".join(parts)

    return system, user_message
