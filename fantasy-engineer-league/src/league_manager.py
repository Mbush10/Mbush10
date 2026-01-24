"""
Fantasy Software Engineer League - League Management System

Handles all league operations including creation, roster management,
matchups, trades, and standings.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import random

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
)


@dataclass
class LeagueManager:
    """
    Central manager for all league operations.

    This class orchestrates the fantasy league, handling everything
    from league creation to weekly scoring.
    """

    # In-memory storage (replace with database in production)
    leagues: dict[str, League] = field(default_factory=dict)
    teams: dict[str, FantasyTeam] = field(default_factory=dict)
    engineers: dict[str, Engineer] = field(default_factory=dict)
    matchups: dict[str, Matchup] = field(default_factory=dict)
    trades: dict[str, Trade] = field(default_factory=dict)
    weekly_scores: dict[str, WeeklyScore] = field(default_factory=dict)
    draft_picks: dict[str, DraftPick] = field(default_factory=dict)

    # ==================== League Operations ====================

    def create_league(
        self,
        name: str,
        commissioner_email: str,
        settings: Optional[LeagueSettings] = None,
        max_teams: int = 10,
    ) -> League:
        """Create a new fantasy league."""
        league = League(
            name=name,
            commissioner_email=commissioner_email,
            settings=settings or LeagueSettings(),
            max_teams=max_teams,
        )
        self.leagues[league.id] = league
        return league

    def get_league(self, league_id: str) -> Optional[League]:
        """Retrieve a league by ID."""
        return self.leagues.get(league_id)

    def update_league_status(self, league_id: str, status: LeagueStatus) -> bool:
        """Update the status of a league."""
        league = self.get_league(league_id)
        if not league:
            return False
        league.status = status
        return True

    def advance_week(self, league_id: str) -> int:
        """Advance the league to the next week."""
        league = self.get_league(league_id)
        if not league:
            return -1

        league.current_week += 1

        # Check for playoff transition
        if league.current_week > league.settings.regular_season_weeks:
            if league.status == LeagueStatus.IN_SEASON:
                league.status = LeagueStatus.PLAYOFFS

        return league.current_week

    # ==================== Team Operations ====================

    def create_team(
        self,
        league_id: str,
        team_name: str,
        manager_name: str,
        manager_email: str,
    ) -> Optional[FantasyTeam]:
        """Create and register a new team in a league."""
        league = self.get_league(league_id)
        if not league or league.is_full:
            return None

        team = FantasyTeam(
            name=team_name,
            manager_name=manager_name,
            manager_email=manager_email,
            league_id=league_id,
        )

        self.teams[team.id] = team
        league.team_ids.append(team.id)

        return team

    def get_team(self, team_id: str) -> Optional[FantasyTeam]:
        """Retrieve a team by ID."""
        return self.teams.get(team_id)

    def get_league_teams(self, league_id: str) -> list[FantasyTeam]:
        """Get all teams in a league."""
        league = self.get_league(league_id)
        if not league:
            return []
        return [self.teams[tid] for tid in league.team_ids if tid in self.teams]

    def set_starting_lineup(
        self, team_id: str, engineer_ids: list[str]
    ) -> bool:
        """Set the starting lineup for a team."""
        team = self.get_team(team_id)
        if not team:
            return False

        # Verify all engineers are on the roster
        for eng_id in engineer_ids:
            if eng_id not in team.roster:
                return False

        team.starting_lineup = engineer_ids
        return True

    # ==================== Engineer Operations ====================

    def add_engineer_to_pool(self, engineer: Engineer) -> Engineer:
        """Add an engineer to the available pool."""
        self.engineers[engineer.id] = engineer
        return engineer

    def get_engineer(self, engineer_id: str) -> Optional[Engineer]:
        """Retrieve an engineer by ID."""
        return self.engineers.get(engineer_id)

    def get_available_engineers(self) -> list[Engineer]:
        """Get all engineers available on the waiver wire."""
        return [e for e in self.engineers.values() if e.is_available]

    def add_engineer_to_team(
        self, team_id: str, engineer_id: str
    ) -> bool:
        """Add an engineer to a team's roster (waiver pickup)."""
        team = self.get_team(team_id)
        engineer = self.get_engineer(engineer_id)

        if not team or not engineer or not engineer.is_available:
            return False

        # Check roster size
        league = self.get_league(team.league_id)
        if league and len(team.roster) >= league.settings.roster_size:
            return False

        team.roster.append(engineer_id)
        engineer.is_available = False
        engineer.fantasy_team_id = team_id

        return True

    def drop_engineer_from_team(
        self, team_id: str, engineer_id: str
    ) -> bool:
        """Drop an engineer from a team's roster."""
        team = self.get_team(team_id)
        engineer = self.get_engineer(engineer_id)

        if not team or not engineer:
            return False

        if engineer_id not in team.roster:
            return False

        team.roster.remove(engineer_id)

        # Remove from starting lineup if present
        if engineer_id in team.starting_lineup:
            team.starting_lineup.remove(engineer_id)

        engineer.is_available = True
        engineer.fantasy_team_id = None

        return True

    # ==================== Draft Operations ====================

    def setup_draft(self, league_id: str, randomize_order: bool = True) -> bool:
        """Initialize the draft for a league."""
        league = self.get_league(league_id)
        if not league:
            return False

        # Set draft order
        if randomize_order:
            league.draft_order = random.sample(
                league.team_ids, len(league.team_ids)
            )
        else:
            league.draft_order = list(league.team_ids)

        # Update team draft positions
        for i, team_id in enumerate(league.draft_order):
            team = self.get_team(team_id)
            if team:
                team.draft_position = i + 1

        # Create draft picks
        self._generate_draft_picks(league)

        league.status = LeagueStatus.DRAFTING
        return True

    def _generate_draft_picks(self, league: League) -> None:
        """Generate all draft picks for a snake draft."""
        total_rounds = league.settings.roster_size
        pick_number = 0

        for round_num in range(1, total_rounds + 1):
            # Snake draft - reverse order on even rounds
            order = league.draft_order
            if round_num % 2 == 0:
                order = list(reversed(order))

            for team_id in order:
                pick_number += 1
                pick = DraftPick(
                    league_id=league.id,
                    round=round_num,
                    pick_number=pick_number,
                    team_id=team_id,
                )
                self.draft_picks[pick.id] = pick

    def make_draft_pick(
        self, league_id: str, team_id: str, engineer_id: str
    ) -> bool:
        """Make a draft selection."""
        # Find the next pick for this team
        pick = self._get_next_pick(league_id, team_id)
        if not pick:
            return False

        engineer = self.get_engineer(engineer_id)
        if not engineer or not engineer.is_available:
            return False

        # Make the pick
        pick.engineer_id = engineer_id
        pick.is_complete = True
        pick.picked_at = datetime.now()

        # Add to team roster
        self.add_engineer_to_team(team_id, engineer_id)

        # Check if draft is complete
        if self._is_draft_complete(league_id):
            league = self.get_league(league_id)
            if league:
                league.status = LeagueStatus.IN_SEASON
                league.current_week = 1

        return True

    def _get_next_pick(
        self, league_id: str, team_id: str
    ) -> Optional[DraftPick]:
        """Get the next uncompleted pick for a team."""
        picks = [
            p
            for p in self.draft_picks.values()
            if p.league_id == league_id
            and p.team_id == team_id
            and not p.is_complete
        ]
        return min(picks, key=lambda p: p.pick_number) if picks else None

    def _is_draft_complete(self, league_id: str) -> bool:
        """Check if all draft picks have been made."""
        league_picks = [
            p for p in self.draft_picks.values() if p.league_id == league_id
        ]
        return all(p.is_complete for p in league_picks)

    # ==================== Matchup Operations ====================

    def generate_weekly_matchups(self, league_id: str, week: int) -> list[Matchup]:
        """Generate matchups for a given week."""
        league = self.get_league(league_id)
        if not league:
            return []

        teams = league.team_ids.copy()
        matchups = []

        # Simple round-robin pairing
        random.shuffle(teams)

        while len(teams) >= 2:
            team_a = teams.pop()
            team_b = teams.pop()

            matchup = Matchup(
                league_id=league_id,
                week=week,
                team_a_id=team_a,
                team_b_id=team_b,
            )
            self.matchups[matchup.id] = matchup
            matchups.append(matchup)

        return matchups

    def get_week_matchups(self, league_id: str, week: int) -> list[Matchup]:
        """Get all matchups for a specific week."""
        return [
            m
            for m in self.matchups.values()
            if m.league_id == league_id and m.week == week
        ]

    def finalize_matchup(self, matchup_id: str) -> Optional[Matchup]:
        """Mark a matchup as complete and update team records."""
        matchup = self.matchups.get(matchup_id)
        if not matchup or matchup.is_complete:
            return None

        matchup.is_complete = True
        winner_id = matchup.determine_winner()

        # Update team records
        team_a = self.get_team(matchup.team_a_id)
        team_b = self.get_team(matchup.team_b_id)

        if team_a and team_b:
            if winner_id == team_a.id:
                team_a.wins += 1
                team_b.losses += 1
            elif winner_id == team_b.id:
                team_b.wins += 1
                team_a.losses += 1
            else:
                team_a.ties += 1
                team_b.ties += 1

            team_a.total_points += matchup.team_a_score
            team_b.total_points += matchup.team_b_score

        return matchup

    # ==================== Trade Operations ====================

    def propose_trade(
        self,
        league_id: str,
        from_team_id: str,
        to_team_id: str,
        engineers_offered: list[str],
        engineers_requested: list[str],
        message: str = "",
    ) -> Optional[Trade]:
        """Create a new trade proposal."""
        trade = Trade(
            league_id=league_id,
            proposing_team_id=from_team_id,
            receiving_team_id=to_team_id,
            engineers_from_proposer=engineers_offered,
            engineers_from_receiver=engineers_requested,
            message=message,
        )
        self.trades[trade.id] = trade
        return trade

    def accept_trade(self, trade_id: str) -> bool:
        """Accept and execute a trade."""
        trade = self.trades.get(trade_id)
        if not trade or trade.status != "pending":
            return False

        # Execute the swap
        proposer = self.get_team(trade.proposing_team_id)
        receiver = self.get_team(trade.receiving_team_id)

        if not proposer or not receiver:
            return False

        # Move engineers from proposer to receiver
        for eng_id in trade.engineers_from_proposer:
            if eng_id in proposer.roster:
                proposer.roster.remove(eng_id)
                receiver.roster.append(eng_id)
                engineer = self.get_engineer(eng_id)
                if engineer:
                    engineer.fantasy_team_id = receiver.id

        # Move engineers from receiver to proposer
        for eng_id in trade.engineers_from_receiver:
            if eng_id in receiver.roster:
                receiver.roster.remove(eng_id)
                proposer.roster.append(eng_id)
                engineer = self.get_engineer(eng_id)
                if engineer:
                    engineer.fantasy_team_id = proposer.id

        trade.status = "accepted"
        trade.resolved_at = datetime.now()
        return True

    def reject_trade(self, trade_id: str) -> bool:
        """Reject a trade proposal."""
        trade = self.trades.get(trade_id)
        if not trade or trade.status != "pending":
            return False

        trade.status = "rejected"
        trade.resolved_at = datetime.now()
        return True

    def veto_trade(self, trade_id: str, voting_team_id: str) -> bool:
        """Cast a veto vote against a trade."""
        trade = self.trades.get(trade_id)
        if not trade or trade.status != "pending":
            return False

        if voting_team_id not in trade.veto_votes:
            trade.veto_votes.append(voting_team_id)

        # Check if enough vetoes to block
        league = self.get_league(trade.league_id)
        if league and len(trade.veto_votes) >= league.settings.veto_votes_required:
            trade.status = "vetoed"
            trade.resolved_at = datetime.now()

        return True

    # ==================== Standings Operations ====================

    def get_standings(self, league_id: str) -> list[FantasyTeam]:
        """Get league standings sorted by record."""
        teams = self.get_league_teams(league_id)

        # Sort by: wins desc, then total points desc
        return sorted(
            teams,
            key=lambda t: (t.wins, t.total_points),
            reverse=True,
        )

    def get_playoff_teams(self, league_id: str) -> list[FantasyTeam]:
        """Get teams that qualify for playoffs."""
        league = self.get_league(league_id)
        if not league:
            return []

        standings = self.get_standings(league_id)
        return standings[: league.settings.playoff_teams]

    # ==================== Scoring Operations ====================

    def record_weekly_score(
        self,
        engineer_id: str,
        league_id: str,
        week: int,
        raw_metrics: dict,
    ) -> WeeklyScore:
        """
        Record an engineer's metrics for a week.

        The actual scoring calculation is handled by the ScoringEngine.
        """
        score = WeeklyScore(
            engineer_id=engineer_id,
            league_id=league_id,
            week=week,
            raw_metrics=raw_metrics,
        )
        self.weekly_scores[score.id] = score
        return score

    def get_engineer_weekly_score(
        self, engineer_id: str, league_id: str, week: int
    ) -> Optional[WeeklyScore]:
        """Get an engineer's score for a specific week."""
        for score in self.weekly_scores.values():
            if (
                score.engineer_id == engineer_id
                and score.league_id == league_id
                and score.week == week
            ):
                return score
        return None

    def calculate_team_weekly_score(
        self, team_id: str, week: int
    ) -> float:
        """Calculate total score for a team's starters in a week."""
        team = self.get_team(team_id)
        if not team:
            return 0.0

        total = 0.0
        for eng_id in team.starting_lineup:
            score = self.get_engineer_weekly_score(
                eng_id, team.league_id, week
            )
            if score:
                total += score.total_points

        return total
