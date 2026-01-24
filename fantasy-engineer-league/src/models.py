"""
Fantasy Software Engineer League - Core Data Models

These models define the structure of the league. Scoring metrics
are intentionally left as placeholders to be configured later.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4


class LeagueStatus(Enum):
    """Status of a league throughout its lifecycle."""
    DRAFT_PENDING = "draft_pending"
    DRAFTING = "drafting"
    IN_SEASON = "in_season"
    PLAYOFFS = "playoffs"
    COMPLETED = "completed"


class RosterSlot(Enum):
    """Types of roster positions."""
    STARTER = "starter"
    FLEX = "flex"
    BENCH = "bench"


class MatchupResult(Enum):
    """Possible outcomes of a weekly matchup."""
    WIN = "win"
    LOSS = "loss"
    TIE = "tie"
    PENDING = "pending"


@dataclass
class Engineer:
    """
    Represents a software engineer in the player pool.

    Engineers are the 'athletes' that get drafted and scored.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    email: str = ""
    team_affiliation: str = ""  # Their actual company/team
    position: str = ""  # e.g., "Backend", "Frontend", "Fullstack", "DevOps"

    # Engineer metadata
    years_experience: int = 0
    primary_language: str = ""
    github_username: Optional[str] = None

    # Fantasy status
    is_available: bool = True  # Available on waiver wire
    fantasy_team_id: Optional[str] = None  # Which fantasy team owns them

    def __repr__(self) -> str:
        return f"Engineer({self.name}, {self.position})"


@dataclass
class FantasyTeam:
    """
    A manager's team in the fantasy league.

    Each manager controls one team and drafts engineers to their roster.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    manager_name: str = ""
    manager_email: str = ""
    league_id: str = ""

    # Roster - engineers assigned to this team
    roster: list[str] = field(default_factory=list)  # List of Engineer IDs

    # Lineup configuration - which roster spots are starters
    starting_lineup: list[str] = field(default_factory=list)  # Engineer IDs in starting positions

    # Season record
    wins: int = 0
    losses: int = 0
    ties: int = 0
    total_points: float = 0.0

    # Draft info
    draft_position: int = 0

    @property
    def record(self) -> str:
        """Return W-L-T record string."""
        return f"{self.wins}-{self.losses}-{self.ties}"

    @property
    def win_percentage(self) -> float:
        """Calculate win percentage."""
        total_games = self.wins + self.losses + self.ties
        if total_games == 0:
            return 0.0
        return (self.wins + (self.ties * 0.5)) / total_games


@dataclass
class Matchup:
    """
    A weekly head-to-head matchup between two fantasy teams.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    league_id: str = ""
    week: int = 0

    # The two competing teams
    team_a_id: str = ""
    team_b_id: str = ""

    # Scores for the week
    team_a_score: float = 0.0
    team_b_score: float = 0.0

    # Result
    is_complete: bool = False
    winner_id: Optional[str] = None  # None if tie or pending

    # Playoff matchup flag
    is_playoff: bool = False
    playoff_round: Optional[str] = None  # "semifinal", "championship", etc.

    def determine_winner(self) -> Optional[str]:
        """Determine and set the winner based on scores."""
        if not self.is_complete:
            return None

        if self.team_a_score > self.team_b_score:
            self.winner_id = self.team_a_id
        elif self.team_b_score > self.team_a_score:
            self.winner_id = self.team_b_id
        else:
            self.winner_id = None  # Tie

        return self.winner_id


@dataclass
class WeeklyScore:
    """
    Score breakdown for an engineer in a given week.

    The actual metrics and point values are configurable.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    engineer_id: str = ""
    week: int = 0
    league_id: str = ""

    # Raw metrics - these will be populated based on configured metrics
    # Using a dict to allow flexible metric definitions
    raw_metrics: dict = field(default_factory=dict)

    # Calculated points per category
    category_points: dict = field(default_factory=dict)

    # Total points for the week
    total_points: float = 0.0

    # Bonus/penalty points
    bonus_points: float = 0.0
    penalty_points: float = 0.0

    calculated_at: Optional[datetime] = None


@dataclass
class LeagueSettings:
    """
    Configurable settings for a league.
    """
    # Roster configuration
    roster_size: int = 6
    starter_slots: int = 4
    flex_slots: int = 1
    bench_slots: int = 1

    # Season configuration
    regular_season_weeks: int = 13
    playoff_weeks: int = 3
    playoff_teams: int = 4

    # Scoring configuration - placeholder structure
    # This is where metrics will be defined
    scoring_categories: list[dict] = field(default_factory=list)

    # Example structure for scoring_categories:
    # [
    #     {"name": "metric_name", "points_per_unit": 1.0, "description": "..."},
    #     ...
    # ]

    # Trade settings
    trade_deadline_week: int = 11
    trade_review_period_hours: int = 24
    veto_votes_required: int = 4

    # Waiver settings
    waiver_priority_type: str = "reverse_standings"  # or "faab", "rolling"

    # Draft settings
    draft_type: str = "snake"  # or "auction", "auto"
    seconds_per_pick: int = 90


@dataclass
class League:
    """
    The main league container that holds all league data and settings.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    commissioner_email: str = ""

    # League configuration
    settings: LeagueSettings = field(default_factory=LeagueSettings)

    # Status
    status: LeagueStatus = LeagueStatus.DRAFT_PENDING
    current_week: int = 0

    # Participants
    team_ids: list[str] = field(default_factory=list)
    max_teams: int = 10

    # Season dates
    season_start: Optional[datetime] = None
    season_end: Optional[datetime] = None

    # Draft info
    draft_date: Optional[datetime] = None
    draft_order: list[str] = field(default_factory=list)  # Team IDs in draft order

    created_at: datetime = field(default_factory=datetime.now)

    @property
    def is_full(self) -> bool:
        """Check if league has reached max teams."""
        return len(self.team_ids) >= self.max_teams


@dataclass
class Trade:
    """
    A trade proposal between two teams.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    league_id: str = ""

    # Teams involved
    proposing_team_id: str = ""
    receiving_team_id: str = ""

    # Engineers being traded
    engineers_from_proposer: list[str] = field(default_factory=list)
    engineers_from_receiver: list[str] = field(default_factory=list)

    # Status
    status: str = "pending"  # pending, accepted, rejected, vetoed, expired

    # Voting
    veto_votes: list[str] = field(default_factory=list)  # Team IDs that voted to veto

    # Timestamps
    proposed_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

    # Optional message
    message: str = ""


@dataclass
class DraftPick:
    """
    Represents a single pick in the draft.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    league_id: str = ""

    round: int = 0
    pick_number: int = 0  # Overall pick number

    team_id: str = ""
    engineer_id: Optional[str] = None  # None until pick is made

    is_complete: bool = False
    picked_at: Optional[datetime] = None


# Type alias for the engineer pool
EngineerPool = list[Engineer]
