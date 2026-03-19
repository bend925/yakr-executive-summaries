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

TONE: Warm but professional. Not corporate, not casual. Like a trusted advisor giving a friend a business update. Use plain English — no jargon, no status codes, no acronyms the client wouldn't know.

FORMAT — follow this structure exactly:
1. Greeting line (provided to you — use it exactly as given).
2. Brief intro line (e.g., "Hope you're well! Just wanted to give you an update on all the visa matters, as well as some ETAs - please see your executive summary below.")
3. Per-candidate sections (for candidates WITH movement/updates):
   - Candidate full name as a bold heading
   - Nomination: [status in plain English + any dates/context from their notes]
   - [Visa subclass number] Visa: [status + context]
   - Skills Assessment: [status + context] (omit line entirely if "not required")
   - 400 Visa: [status] (only include this line if the candidate actually has a 400 visa in progress or it's applicable to their pathway — otherwise omit entirely)
   - ETA: [range based on processing times table provided] [REVIEW - verify current DHA processing times at https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-processing-times/global-visa-processing-times]
   - Challenges: (only if there are blockers worth mentioning to the client)
   - Next Steps: (only if there are decisions needed or upcoming milestones)
4. Condensed "no movement" block for candidates with nothing new — use exactly this format:
   "The following candidates' applications are lodged and processing with the Department — no action required from your end at this stage:"
   - Bullet list: each bullet is "Name (visa type, lodged DD Month YYYY)"
5. ACTION ITEMS section (only if there are genuine decisions or actions needed from the client):
   - Be specific about what you need from them
   - If no action items, omit this section entirely
6. Warm sign-off like "Let me know if you have any questions, or otherwise have a fantastic day ahead!" then "Kind regards," and "Joe."

CRITICAL RULES:
- NEVER include internal file references (C003, Y001, etc.)
- NEVER include internal team member names (Erika, Deisy, Gabriel, or any team references)
- NEVER include hours worked, budgets, or capacity planning metadata
- NEVER include Bot_Doc_Status or Bot_QA_Notes content
- NEVER auto-generate subclass 400 visa recommendations or suggest preparing a 400. If a candidate already has a 400 in progress, mention its status factually. Otherwise do NOT suggest one. If you think a 400 might be worth considering, just add [REVIEW - consider 400 recommendation?] as a note — do not write the recommendation itself.
- For any strategic recommendation or decision point that requires migration expertise, insert [REVIEW - brief reason] so the human reviewer can decide whether to include it. Do NOT write the strategic recommendation itself.
- For ALL ETAs, present as a range and add [REVIEW - verify current DHA processing times at https://immi.homeaffairs.gov.au/visas/getting-a-visa/visa-processing-times/global-visa-processing-times]
- For notes marked [SENSITIVE], wrap the relevant content in [REVIEW - sensitive note, check before including]
- Where a candidate is unresponsive or not progressing, DO surface this clearly — clients need to know
- Where documents are missing or payment is outstanding from the client side, DO surface this
- Present processing times as "as per current Department processing times, we'd expect a decision within X to Y months from lodgement"
- Calculate ETAs by: for Preparing candidates, estimate from likely lodgement date + processing time. For Processing candidates, calculate from Date Visa Lodged + processing time.
- Do NOT open with "Hi" — use "Morning" or "Afternoon" as provided in the greeting.

407 TRAINING VISA UPDATE (as at March 2026):
The 407 Training Visa now requires mandatory sequential lodgement — sponsorship must be approved first, then nomination must be approved, then visa can be lodged. Previously these could be lodged concurrently. This significantly extends end-to-end timelines. The refusal rate has also risen to ~45% in FY 2025-26 due to increased scrutiny. For any 407 candidates, reflect this context in their section — mention the sequential requirement and elevated refusal risk where relevant."""


# ---------------------------------------------------------------------------
# Example Email (style reference)
# ---------------------------------------------------------------------------

STYLE_REFERENCE = """## Style Reference — Example Email (this is the gold standard for tone, format, and detail level)

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

Joe."""


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

def build_prompt(client: Client, greeting: str = "Morning") -> tuple[str, str]:
    """Build the system prompt and user message for a client summary.

    Returns (system_prompt, user_message).
    """
    active = client.active_candidates
    no_movement = client.no_movement_candidates

    # Build user message
    parts = [
        f"Generate an executive summary email for **{client.company_name}**.",
        f"Use this greeting: \"{greeting} [Name],\"",
        "",
        "## Processing Time Reference",
        get_processing_times_table(),
        "",
    ]

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

    parts.append(STYLE_REFERENCE)

    user_message = "\n".join(parts)

    return SYSTEM_PROMPT, user_message
