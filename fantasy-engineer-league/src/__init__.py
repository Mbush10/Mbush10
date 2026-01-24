"""
Fantasy Software Engineer League

A fantasy sports-style league for software engineers.
"""

from models import (
    League,
    LeagueSettings,
    LeagueStatus,
    FantasyTeam,
    Engineer,
    Matchup,
    Trade,
    DraftPick,
    WeeklyScore,
    RosterSlot,
    MatchupResult,
)

from league_manager import LeagueManager

from scoring_engine import (
    ScoringEngine,
    ScoringConfiguration,
    ScoringMetric,
    MetricType,
    create_github_focused_config,
    create_agile_focused_config,
    create_quality_focused_config,
)

__version__ = "0.1.0"

__all__ = [
    # Models
    "League",
    "LeagueSettings",
    "LeagueStatus",
    "FantasyTeam",
    "Engineer",
    "Matchup",
    "Trade",
    "DraftPick",
    "WeeklyScore",
    "RosterSlot",
    "MatchupResult",
    # Manager
    "LeagueManager",
    # Scoring
    "ScoringEngine",
    "ScoringConfiguration",
    "ScoringMetric",
    "MetricType",
    "create_github_focused_config",
    "create_agile_focused_config",
    "create_quality_focused_config",
]
