"""
Data models for candidates and clients.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Candidate:
    """A single candidate with merged data from all source sheets."""

    file_name: str                          # C003, Y001 etc (internal only, never output)
    given_names: str
    family_names: str
    company: str
    visa_type: str                          # raw Type column value
    sheet_source: str                       # "preparing" | "processing" | "finalised" | "paused"

    # Statuses (raw codes — translated by filters.py before prompt)
    nomination_status: Optional[str] = None
    visa_status: Optional[str] = None
    other_app_status: Optional[str] = None
    sa_status: Optional[str] = None

    # Dates
    visa_lodged_date: Optional[date] = None
    visa_finalised_date: Optional[date] = None

    # Notes from Active Visa Matters
    notes: str = ""
    extra_notes: str = ""

    # Occupation (from Preparing or SA sheet)
    occupation: str = ""

    # Skills Assessment detail (from SA / S.A. Completed sheets)
    sa_progress: Optional[float] = None     # 0–1 decimal
    sa_notes: str = ""

    # Capacity Planning (from team sheets)
    recent_tasks: list[str] = field(default_factory=list)
    task_notes: list[str] = field(default_factory=list)

    # Lodgement queue
    lodgement_status: Optional[str] = None
    lodgement_comments: Optional[str] = None

    # Derived (set by filters.py)
    has_movement: bool = True
    is_sensitive: bool = False

    @property
    def full_name(self) -> str:
        return f"{self.given_names} {self.family_names}".strip()


@dataclass
class Client:
    """A client company (or branch) with its associated candidates."""

    company_name: str
    parent_company: Optional[str] = None    # set if this is a branch
    branch: Optional[str] = None
    candidates: list[Candidate] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        if self.parent_company and self.branch and self.branch != self.company_name:
            return f"{self.parent_company} > {self.branch}"
        return self.company_name

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    @property
    def active_candidates(self) -> list[Candidate]:
        return [c for c in self.candidates if c.has_movement]

    @property
    def no_movement_candidates(self) -> list[Candidate]:
        return [c for c in self.candidates if not c.has_movement]
